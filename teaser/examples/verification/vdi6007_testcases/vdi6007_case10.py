#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os
import numpy as np

import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_VDI
import teaser.examples.verification.vdi6007_testcases.vdi6007_case01 as vdic
import teaser.logic.simulation.VDI_6007.equal_air_temperature as eq_air_temp


def run_case10(plot_res=False):
    """
    Run test case 10

    Parameters
    ----------
    plot_res : bool, optional
        Defines, if results should be plotted (default: False)

    Returns
    -------
    result_tuple : tuple (of floats)
        Results tuple with maximal temperature deviations
        (max_dev_1, max_dev_10, max_dev_60)
    """

    # Definition of time horizon
    times_per_hour = 60
    timesteps = 24 * 60 * times_per_hour  # 60 days
    timesteps_day = int(24 * times_per_hour)

    # Zero inputs
    ventRate = np.zeros(timesteps)
    sunblind_in = np.zeros((timesteps, 1))
    solarRad_wall = np.zeros((timesteps, 1))

    # Constant inputs
    alphaRad = np.zeros(timesteps) + 5
    t_black_sky = np.zeros(timesteps) + 273.15

    # Variable inputs
    Q_ig = np.zeros(timesteps_day)
    source_igRad = np.zeros(timesteps_day)
    for q in range(int(7 * timesteps_day / 24), int(17 * timesteps_day / 24)):
        Q_ig[q] = 200 + 80
        source_igRad[q] = 80
    Q_ig = np.tile(Q_ig, 60)
    source_igRad = np.tile(source_igRad, 60)

    this_path = os.path.dirname(os.path.abspath(__file__))
    ref_file = 'case10_q_sol.csv'
    ref_path = os.path.join(this_path, 'inputs', ref_file)

    q_sol_rad_win_raw = np.loadtxt(ref_path, usecols=(1,))
    solarRad_win = q_sol_rad_win_raw[0:24]
    solarRad_win[solarRad_win > 100] = solarRad_win[solarRad_win > 100] * 0.15
    solarRad_win_adj = np.repeat(solarRad_win, times_per_hour)
    solarRad_win_in = np.array([np.tile(solarRad_win_adj, 60)]).T

    ref_file = 'case10_t_amb.csv'
    ref_path = os.path.join(this_path, 'inputs', ref_file)

    t_outside_raw = np.loadtxt(ref_path, delimiter=",")
    t_outside = ([t_outside_raw[2 * i, 1] for i in range(24)])
    t_outside_adj = np.repeat(t_outside, times_per_hour)
    weatherTemperature = np.tile(t_outside_adj, 60)

    equ_air_params = {"aExt": 0.7,
                      "eExt": 0.9,
                      "wfWall": [0.04646093176283288, ],
                      "wfWin": [0.32441554918476245, ],
                      "wfGro": 0.6291235190524047,
                      "T_Gro": 273.15 + 15,
                      "alpha_wall_out": 20,
                      "alpha_rad_wall": 5,
                      "withLongwave": False}

    equalAirTemp = eq_air_temp.equal_air_temp(HSol=solarRad_wall,
                                              TBlaSky=t_black_sky,
                                              TDryBul=weatherTemperature,
                                              sunblind=sunblind_in,
                                              params=equ_air_params)

    # Load constant house parameters
    houseData = {"R1i": 0.000779671554640369,
                 "C1i": 12333949.4129606,
                 "Ai": 58,
                 "RRest": 0.011638548,
                 "R1o": 0.00171957697767797,
                 "C1o": 4338751.41,
                 "Ao": [28],
                 "Aw": np.zeros(1),
                 "At": [7, ],
                 "Vair": 52.5,
                 "rhoair": 1.19,
                 "cair": 0,
                 "splitfac": 0.09,
                 "g": 1,
                 "alphaiwi": 2.12,
                 "alphaowi": 2.398,
                 "alphaWall": 28 * 9.75,  # 28 * sum(Ao)
                 "withInnerwalls": True}

    krad = 1

    # Define set points (prevent heating or cooling!)
    t_set_heating = np.zeros(timesteps)  # in Kelvin
    t_set_cooling = np.zeros(timesteps) + 600  # in Kelvin

    heater_limit = np.zeros((timesteps, 3)) + 1e10
    cooler_limit = np.zeros((timesteps, 3)) - 1e10

    # Calculate indoor air temperature
    T_air, Q_hc, Q_iw, Q_ow = \
        low_order_VDI.reducedOrderModelVDI(houseData,
                                           weatherTemperature,
                                           solarRad_win_in,
                                           equalAirTemp,
                                           alphaRad,
                                           ventRate,
                                           Q_ig,
                                           source_igRad,
                                           krad,
                                           t_set_heating,
                                           t_set_cooling,
                                           heater_limit,
                                           cooler_limit,
                                           heater_order=np.array(
                                               [1, 2,
                                                3]),
                                           cooler_order=np.array(
                                               [1, 2,
                                                3]),
                                           dt=int(
                                               3600 / times_per_hour),
                                           T_air_init=273.15 + 17.6,
                                           T_iw_init=273.15 + 17.6,
                                           T_ow_init=273.15 + 17.6)

    # Compute averaged results
    T_air_c = T_air - 273.15
    T_air_mean = np.array(
        [np.mean(T_air_c[i * times_per_hour:(i + 1) * times_per_hour]) for i in
         range(24 * 60)])

    T_air_1 = T_air_mean[0:24]
    T_air_10 = T_air_mean[216:240]
    T_air_60 = T_air_mean[1416:1440]

    ref_file = 'case10_res.csv'
    ref_path = os.path.join(this_path, 'inputs', ref_file)

    # Load reference results
    (T_air_ref_1, T_air_ref_10, T_air_ref_60) = vdic.load_res(ref_path)
    T_air_ref_1 = T_air_ref_1[:, 0]
    T_air_ref_10 = T_air_ref_10[:, 0]
    T_air_ref_60 = T_air_ref_60[:, 0]

    # Plot comparisons
    def plot_result(res, ref, title="Results day 1"):

        import matplotlib.pyplot as plt

        plt.figure()
        ax_top = plt.subplot(211)
        plt.plot(res, label="Reference", color="black", linestyle="--")
        plt.plot(ref, label="Simulation", color="blue", linestyle="-")
        plt.legend()
        plt.ylabel("Temperature in degC")

        plt.title(title)

        plt.subplot(212, sharex=ax_top)
        plt.plot(res - ref, label="Ref. - Sim.")
        plt.legend()
        plt.ylabel("Temperature difference in K")
        plt.xticks([4 * i for i in range(7)])
        plt.xlim([1, 24])
        plt.xlabel("Time in h")

        plt.show()

    if plot_res:
        plot_result(T_air_1, T_air_ref_1, "Results day 1")
        plot_result(T_air_10, T_air_ref_10, "Results day 10")
        plot_result(T_air_60, T_air_ref_60, "Results day 60")

    max_dev_1 = np.max(np.abs(T_air_1 - T_air_ref_1))
    max_dev_10 = np.max(np.abs(T_air_10 - T_air_ref_10))
    max_dev_60 = np.max(np.abs(T_air_60 - T_air_ref_60))

    print("Max. deviation day 1: " + str(max_dev_1))
    print("Max. deviation day 10: " + str(max_dev_10))
    print("Max. deviation day 60: " + str(max_dev_60))

    return (max_dev_1, max_dev_10, max_dev_60)


if __name__ == '__main__':
    run_case10(plot_res=True)
