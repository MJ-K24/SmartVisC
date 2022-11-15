"""
[Mission 1]
Based on the traditional(or conventional) iVT filter process, customize it!
    - Raw Gaze Point --> Raw Fixation


Notation:
    - RP: Raw gaze Point
    - RF : Raw Fixation
"""
from utils.data import RawFixation
import scipy.signal as signal
# from scipy import signal
import numpy as np
import pandas as pd
import env
import params
from collections import defaultdict
from utils.visual import show_line_plot, show_line_plot_compare
from sklearn.metrics import pairwise_distances


def get_xs(obj: list):
    return np.array([i.x for i in obj])


def get_ys(obj: list):
    return np.array([i.y for i in obj])


def get_time(obj: list):
    return np.array([i.timestamp for i in obj])


def get_delta(obj, window=2):
    delta = np.lib.stride_tricks.sliding_window_view(obj, window, writeable=True)
    delta = delta[:, -1] - delta[:, 0]
    return delta


def gap_fill_in(rps):
    # TBD: Gap fill in 구현이 이미 되어 있는 데이터의 상태. 추후에 데이터를 받게 되면 구현해야할 필요 가능
    # Parameter: Max Gap Length as mgl
    """
    :param rps: List<RawGazePoint>
    :return: List<RawGazePoint>
    다만 여기서 rps의 내부에서 값들의 업데이트나 변경사항이 있다면 알려주기
    ex. null value를 어떻게 interpolation을 했다.

    ver.0.1 : 최근 데이터를 보았을 때 일단 blink는 모두 다 false이지만
     일부 x,y값이 -9999인 경우가 존재해서 해당 점들의 x,y는 None으로 앞서 처리함. 이것에 대한 interpolation이 필요
     일단은 무식하게 linear interpolation을 하고 맨 처음부터 NaN인 좌표는 backfill을 이용
    """
    mgl = params.max_gap_length
    xs = get_xs(rps)
    ys = get_ys(rps)

    df = pd.DataFrame([xs, ys], index=["X", "Y"]).T
    df.interpolate(inplace=True)
    df.fillna(method="bfill", inplace=True)
    for rp, x, y in zip(rps, df["X"].tolist(), df["Y"].tolist()):
        rp.x = x
        rp.y = y
    
    return rps


def noise_reduction(rps):
    # Parameter: Window size for Moving average
    """
    :param rps: List<RawGazePoint>
    :return: List<RawGazePoint>
    Baseline으로 현재 Moving average를 한 값으로 기존의 값을 업데이트 진행
        - 사실 신호에 대해 convolution연산을 하는 것과 비슷한 것
    """
    xs = get_xs(rps)
    ys = get_ys(rps)

    # # 방법 1: avg
    # window_size = params.window_size
    # window = np.ones(window_size)/window_size
    # xs_new = signal.convolve(xs, window, mode="same")
    # ys_new = signal.convolve(ys, window, mode="same")
    # for rp, x, y in zip(rps, xs_new, ys_new):
    #     rp.x = x
    #     rp.y = y

    # # NOTE: ver.0.1: noise reduction 효과에 따라 시계열 그림으로 나타냄.
    # if env.SHOW_ALL_PLOTS:
    #     show_line_plot_compare(xs, xs_new, f"Noise Reduction, X with window size = {window_size}")
    #     show_line_plot_compare(ys, ys_new, f"Noise Reduction, Y with window size = {window_size}")
    #방법 2 : Exponential smoothing
    #t 시점의 actual 관측치 * alpha + t-1 예측값 *( 1-alpha)

    alpha= 0.7 #alpha값은 메트릭을 고려하여 추후 변경 
    xs_new= [0]*len(xs)
    ys_new= [0]*len(ys)
    for idx,i,in enumerate(xs_new):
        if idx==0:
            xs_new[idx]= xs[0]
        else: 
            xs_new[idx] = alpha* (xs[idx])+ (1-alpha)*(xs_new[idx-1]) 
    for idx,i,in enumerate(ys_new):
        if idx==0:
            ys_new[idx]= ys[0]
        else: 
            ys_new[idx] = alpha* (ys[idx])+ (1-alpha)*(ys_new[idx-1]) 

    for rp, x, y in zip(rps, xs_new, ys_new):
        rp.x = x
        rp.y = y

    return rps

    # #방법 3 simple kalman filter
    
    # ''' params :
    # A : 이전값을 통해 추정값을 예측할때 사용되는 행렬 
    # P : 예측한 값에 대한 오차의 공분산
    # Q : 시스템 노이즈  
    # R : 측정값 노이즈 
    # H : 예측값을 측정값으로 변환할때 사용되는 행렬  
    # K : 칼만이득 => 추정치 - 오차공분산 
    # '''

    # # initial value 
    # A= 1
    # H= 1 
    # Q= np.var(xs)
    # R= np.var(xs)
    # # initial estimate 
    # x_0 = xs[0]
    # y_0 = ys[0]
    # P_0 = 1
    # Kx_0 = 1
    # Ky_0 = 1


    # # z meas - >관측값 
    # def kalman_filter(z_meas, x_esti, P):
    # # (1) Prediction.
    #     x_pred = A * x_esti
    #     P_pred = A * P * A + Q

    # # (2) Kalman Gain.
    #     K = P_pred * H / (H * P_pred * H + R)

    # # (3) Estimation.
    #     x_esti = x_pred + K * (z_meas - H * x_pred)

    # # (4) Error Covariance.
    #     P = P_pred - K * H * P_pred

    #     return x_esti, P, K

    
    # xs_new= [0]*len(xs)
    # ys_new= [0]*len(ys)


    # for idx,i in enumerate(xs_new):
    #     if idx==0:
    #         xs_new[idx], P , K= x_0,P_0 ,Kx_0
    #     else:
    #         xs_new[idx],P, K = kalman_filter(xs[idx],xs_new[idx-1],P)

    # for idx, i in enumerate(ys_new):
    #     if idx ==0 :
    #         ys_new[idx],P,K = y_0,P_0,Ky_0
    #     else:
    #         ys_new[idx],P, K = kalman_filter(ys[idx],ys_new[idx-1],P)

    # for rp, x, y in zip(rps, xs_new, ys_new):
    #     rp.x = x
    #     rp.y = y

    # return rps




def calculate_velocity(rps):
    # Parameter : window length(baseline에는 아직 적용하지 않음)
    """
    :param rps: List<RawGazePoint>
    :return: List<RawGazePoint>
    Baseline으로 단순히 1step간의 차이를 속력으로 계산 및 업데이트
    다만 이 속력 계산시 구간에 대한 parameter를 어떻게 적용하는지에 따라서 달라질 것 같은데
    해당 내용은 완벽히 숙지한 것은 아니에요..! 그래서 구현하실 때 해당 파트 디테일하게 보고 적용해도 될 것 같습니다.
    """

    window_len = params.window_len

    times = get_time(rps)
    xs = get_xs(rps)
    ys = get_ys(rps)

    delta_time = get_delta(times, window_len)
    delta_x = get_delta(xs, window_len)
    # TODO: 이렇게 하면 delta_x==0 인 경우 존재해서 일단 그런 경우는 1로 처리하게 놔둠... 이것도 바꿔야함.
    delta_x[delta_x == 0] = 1

    delta_y = get_delta(ys, window_len)
    # NOTE: 그런데, 여기서 속력이 아니라 속도를 구한다면..?!
    speeds = np.abs(delta_y / delta_x)
    # NA 값 처리
    # TODO: 어떻게 값을 처리할지 정해야 함. 시간 계산을 하게 되면 window_len 만큼 값이 비게 된다!
    #   현재는 0으로 채우는 상태
    speeds = np.append(speeds, [0]*(len(rps)-len(speeds)))
    assert len(speeds) == len(rps), "속도 계산 시 null 값을 처리해주세요!"

    # 각 point에 대해 속력값 업데이트
    for rp, speed in zip(rps, speeds):
        setattr(rp, "speed", speed)

    if env.SHOW_ALL_PLOTS:
        show_line_plot(speeds, f"Speed plot with window length = {window_len}")
    return rps


def absolute_threshold(rps):
    # Parameter : Velocity Threshold
    """
    :param rps: List<RawGazePoint>
    :return: List<RawGBazePoint>
    Baseline으로 단순히 해당 threshold를 넘으면 saccade 아래면 fixation으로 설정
    """
    for rp in rps:
        if rp.speed > params.velocity_threshold:
            setattr(rp, "label", "saccade")
        else:
            setattr(rp, "label", "fixation")
    return rps


def merge_adj_fixation(rps):
    # Parameter: Max time between fixations
    # 추가로 cluster threshold, The Number of neighbors 를 사용
    """
    :param rps: List<RawGazePoint>
    :return: List<RawGazePoint>
    Fixation 사이 Max time: 지금은 죄다 33, 34라서 문제라서 Deprecated된 코드는 사용하지 못하고 있음
    새로 데이터를 받았을 때 확인해봐야 하는 부분.

    Baseline으로 인접하다고 묶인 경우에 대해서 fix_group_id라는 attr를 업데이트 함!
    즉 각 작은 점들마다 합쳐서 하나의 점들로 생각할 경우에는 동일한 fix_group_id를 가지도록

    cluste
    """

    # # Deprecated
    # times = np.array([int(i.timestamp) for i in rps])
    # delta_t = np.lib.stride_tricks.sliding_window_view(times, 2, writeable=True)
    # delta_t = delta_t[:, 1] - delta_t[:, 0]
    # fix_group_id = (delta_t > params.max_time_between_fixations).astype(int).cumsum()

    ###########################################################################
    # Euclidean distance를 기준으로 묶는 과정
    # 다만 어떤 기준으로 묶는지는 임시로 구현해놓은 것

    cluster_thr = params.cluster_thr
    num_neighbor = params.num_neighbor

    xs = get_xs(rps)[:, np.newaxis]
    ys = get_ys(rps)[:, np.newaxis]
    coors = np.concatenate((xs, ys), axis=1)
    distance_mat = pairwise_distances(coors)

    # 임시로 정한 metric
    nth_neighbor = np.sort(distance_mat, axis=1)[:, 1]
    fix_group_id = (nth_neighbor < cluster_thr).astype(int).cumsum()

    # NA 값 처리
    fix_group_id = np.append(fix_group_id, fix_group_id[-1])
    ###########################################################################

    # 값 업데이트
    for rp, group_id in zip(rps, fix_group_id):
        setattr(rp, "fix_group_id", group_id)
    return rps


def discard_short_fixation(rps):
    # Parameter : Minimum fixation parameter as min_fix_duration
    """
    :param rps: List<RawGazePoint>
    :return: List<RawFixation>

    해당 과정에서 Raw Fixation을 반환하게 됨.
    Baseline에서는 그냥 merge해놓은 동일한 group만 반환하고 있고,
    실제로 거리에 따라서 버리는 것은 구현되어 있지 않음.

    RawFixation을 만들기 위해선
    (x, y, timestamp, duration)이 필수요소로, 이를 만들어 주는 코드가 같이 구현되어야 함.
    """
    min_fix_duration = params.min_fix_duration

    # NOTE: 전처리된 rps에서 이제 골라서 duration까지 구하는 것 포함
    fix_groups = defaultdict(lambda: defaultdict(list))
    for rp in rps:
        fix_groups[rp.fix_group_id]["x"].append(rp.x)
        fix_groups[rp.fix_group_id]["y"].append(rp.y)
        fix_groups[rp.fix_group_id]["timestamp"].append(int(rp.timestamp))

    rf_inputs = list(map(lambda fix_group: {
        "x": np.median(fix_group['x']),
        "y": np.median(fix_group['y']),
        "timestamp": np.max(fix_group['timestamp']),
        "duration": np.max(fix_group['timestamp']) - np.min(fix_group['timestamp'])
    }, fix_groups.values()))

    rfs = [RawFixation(rf_input) for rf_input in rf_inputs]
    return rfs


def get_rf(rps):
    """
    Description:

    :param rps: List<RawGazePoint> Raw Gaze Point
    :return: List<RawFixation> Raw Fixation
    """
    # Gap Fill In: 현재 모든 데이터에서 좌표가 다 있는 상태라서 굳이 구현하지 않아도 될듯
    rps = gap_fill_in(rps)

    rps = noise_reduction(rps)
    rps = calculate_velocity(rps)
    rps = absolute_threshold(rps)
    rps = merge_adj_fixation(rps)
    rfs = discard_short_fixation(rps)
    return rfs


def run(rps):
    """
    :param rps: List<RawGazePoint> Raw gaze Point
    :return: rfs: List<RawFixation> Raw Fixation

    현재 단순히 raw fixation만 작동하게 되어 있는데, 데이터가 들어오는 것에 따라서
    전처리나 후처리 등의 과정이 추가될 수도 있는 상태.
    """

    # 전처리
    #   - Blink 처리가 아마 여기서 필요하지 않을까 생각
    # ver.0.1: 현재 데이터에서 x나 y값이 -9999로 찍히는게 존재. 이거에 대한 처리가 필요
    for rp in rps:
        if rp.x == -9999 or rp.y == -9999:
            rp.x = np.nan
            rp.y = np.nan

    # Raw Gaze Point --> Raw Fixation
    rfs = get_rf(rps)

    # 후처리(TBD)

    return rfs
