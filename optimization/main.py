import traceback
import os
import numpy as np
from data_loader import load_data_for_area, get_target_areas
import solver_engine as se
import visualization as viz
from config import Config


def main():
    Config.validate()

    areas = get_target_areas()
    if not areas:
        print("No service areas found.")
        return

    # Create region folder name from the total load file
    base_name = os.path.splitext(os.path.basename(Config.path_total_load))[0]
    region_name = base_name[:3] if len(base_name) >= 3 else base_name

    base_output_dir = Config.result_dir
    region_folder = os.path.join(base_output_dir, region_name)

    if not os.path.exists(region_folder):
        os.makedirs(region_folder)
        print(f"Created region folder: {region_folder}")

    print(f"Detected {len(areas)} service areas, starting computation")

    aggregated_results = {
        "min_cost": [],
        "min_carb": [],
        "knee_point": [],
    }

    all_areas_pareto_info = []

    # Save interval (every N areas)
    SAVE_INTERVAL = 10
    for idx, target_area in enumerate(areas):
        area_folder = os.path.join(region_folder, target_area)
        done_flag_file = os.path.join(area_folder, f"{target_area}_hourly_system_data.xlsx")

        if os.path.exists(done_flag_file):
            print(
                f">>> [{idx+1}/{len(areas)}] Service area {target_area} results already exist, skipping..."
            )
            continue
        print(f"\n>>> [{idx+1}/{len(areas)}] Processing service area: {target_area}")
        try:
            # Create service area subfolder
            if not os.path.exists(area_folder):
                os.makedirs(area_folder)

            # Load data
            d_pv, d_load, d_price, pv_cap_kW, ratio_roof, ratio_shell, city_name = (
                load_data_for_area(target_area)
            )
            if d_pv is None:
                continue

            # Compute key points and hourly data

            # No battery baseline (grid-only)
            res_no_bat = se.run_no_battery_scenario(d_load, d_price)
            # Cost optimal
            cap_eco, cost_eco, carb_eco, df_eco = se.run_min_cost(
                d_pv, d_load, d_price, pv_cap_kW, ratio_roof, ratio_shell
            )
            dict_eco = {"cap": cap_eco, "cost": cost_eco, "carb": carb_eco}

            # Carbon optimal
            cap_carb, cost_carb, carb_carb, df_carb = se.run_min_carbon(
                d_pv,
                d_load,
                d_price,
                pv_cap_kW,
                ratio_roof,
                ratio_shell,
                target_min_carb=None,
            )
            dict_carb = {"cap": cap_carb, "cost": cost_carb, "carb": carb_carb}

            # Pareto scan
            print("Scanning Pareto curve...")
            pareto_results = se.run_epsilon_constraint(
                d_pv,
                d_load,
                d_price,
                pv_cap_kW,
                ratio_roof,
                ratio_shell,
                carb_min=carb_carb,
                carb_max=carb_eco,
                cost_min=cost_eco,
                cost_max=cost_carb,
                n_points=50,
                explicit_boundaries=[dict_eco, dict_carb],
            )

            if not pareto_results:
                print(f"  {target_area} Pareto scan failed, skipping")
                continue

            # Find knee point
            p_costs = np.array([r["cost"] for r in pareto_results])
            p_carbs = np.array([r["carb"] for r in pareto_results])
            knee_idx = viz.find_knee_point_index(p_costs, p_carbs)
            knee_data = pareto_results[knee_idx]
            print(f"  Compromise point: Cap={knee_data['cap']:.1f}, Cost={knee_data['cost']:.0f}")

            # Collect plot data
            all_areas_pareto_info.append(
                {
                    "area": target_area,
                    "city": city_name,
                    "results": pareto_results,
                    "knee_idx": knee_idx,
                }
            )

            # Recompute at knee point
            cap_knee, cost_knee, carb_knee, df_knee = se.run_fixed_capacity(
                d_pv,
                d_load,
                d_price,
                pv_cap_kW,
                ratio_roof,
                ratio_shell,
                target_cap=knee_data["cap"],
                carbon_cap=knee_data["target"],
            )

            # Export files and images
            viz.save_pareto_details(target_area, pareto_results, knee_idx, area_folder)

            hourly_dicts = {
                "Cost_Optimal": df_eco,
                "Carbon_Optimal": df_carb,
                "Compromise": df_knee,
            }
            viz.save_hourly_details(target_area, hourly_dicts, area_folder)

            viz.plot_pareto_curve(
                target_area,
                pareto_results,
                knee_idx,
                area_folder,
                no_bat_data=res_no_bat,
            )

            # Collect aggregated data
            def _pkg(cap, df_res):
                return viz.package_result_row(
                    target_area, cap, pv_cap_kW, ratio_roof, ratio_shell, df_res
                )

            aggregated_results["min_cost"].append(_pkg(cap_eco, df_eco))
            aggregated_results["min_carb"].append(_pkg(cap_carb, df_carb))
            aggregated_results["knee_point"].append(_pkg(cap_knee, df_knee))

            # Periodically save aggregated results
            # If interrupted, current aggregated_results will still be saved
            if (idx + 1) % SAVE_INTERVAL == 0 or (idx + 1) == len(areas):
                print(f"  >> [Auto-save] Processed {idx + 1} areas, updating temporary summary...")
                viz.save_aggregated_excel(
                    aggregated_results, region_folder, region_name
                )

        except Exception as e:
            print(f"{target_area} processing failed: {e}")
            traceback.print_exc()
            continue

    # Plot combined Pareto for this run
    if all_areas_pareto_info:
        print("Plotting combined Pareto curve for this run...")
        viz.plot_combined_pareto(region_name, all_areas_pareto_info, region_folder)

    print("\n>>> Run completed.")


if __name__ == "__main__":
    main()
