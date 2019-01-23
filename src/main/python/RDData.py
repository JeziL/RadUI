import numpy as np
import pandas as pd

AX_LABEL = {
    "threatId": "威胁 ID",
    "Time": "时间 (s)",
    "radialDistance": "距离 (m)",
    "velocity": "速度 (m/s)",
    "azimuth": "水平角 (°)",
    "elevation": "俯仰角 (°)",
    "x": "x",
    "y": "y",
    "z": "z"
}


class RDData:
    def __init__(self, filename):
        pd.set_option("mode.chained_assignment", None)
        with open(filename, "r") as f:
            self.df = pd.read_csv(f, sep="\t")
        self.rdGroup = self.df.groupby("radId")
        self.data = {}
        self.fit_param = {}
        for rdId, group in self.rdGroup:
            rad = group[group["threatId"] > 0][
                ["threatId", "Time", "radialDistance", "velocity", "azimuth", "elevation"]]
            rad = RDData.polar_to_cartesian(rad)
            rad = rad.reset_index(drop=True)
            self.data[rdId] = rad

    @staticmethod
    def polar_to_cartesian(df):
        df["x"] = df.apply(lambda d: d.radialDistance * np.cos(np.deg2rad(d.elevation)) * np.cos(np.deg2rad(d.azimuth)),
                           axis=1)
        df["y"] = df.apply(lambda d: d.radialDistance * np.cos(np.deg2rad(d.elevation)) * np.sin(np.deg2rad(d.azimuth)),
                           axis=1)
        df["z"] = df.apply(lambda d: d.radialDistance * np.sin(np.deg2rad(d.elevation)), axis=1)
        return df

    @property
    def radar_count(self):
        return len(self.rdGroup)

    @property
    def available_radar(self):
        return list(self.rdGroup.groups.keys())

    def info(self):
        ret = []
        for i in self.available_radar:
            ret.append("{0} 号雷达：{1} 点".format(i, len(self.data[i].index)))
        return "\n".join(ret)

    def fit(self, rad_id, stop=40, r=0.97, a=1):
        self.fit_param[rad_id] = {"P": [], "TH": []}
        for i in range(3):
            self.fit_param[rad_id]["P"].append(10e5 * np.eye(2))
            self.fit_param[rad_id]["TH"].append(np.zeros((2, 2)))
        for _, d in self.data[rad_id].iterrows():
            if d.radialDistance <= stop:
                break
            ps = np.matrix([d.radialDistance, 1])
            y_3d = [np.matrix([d.x, 1]), np.matrix([d.y, 1]), np.matrix([d.z, 1])]
            for i in range(3):
                y = y_3d[i]
                ll = 1 / r * np.dot(self.fit_param[rad_id]["P"][i], ps.T) * np.linalg.inv(
                    1 / a + 1 / r * np.linalg.multi_dot([ps, self.fit_param[rad_id]["P"][i], ps.T]))
                self.fit_param[rad_id]["P"][i] = 1 / r * np.dot((np.eye(2) - np.dot(ll, ps)),
                                                                self.fit_param[rad_id]["P"][i])
                self.fit_param[rad_id]["TH"][i] = self.fit_param[rad_id]["TH"][i] + np.dot(ll, (
                            y - np.dot(ps, self.fit_param[rad_id]["TH"][i])))

    def plot_fitting(self, var, axes, rad_id, x="radialDistance"):
        rad = self.data[rad_id]
        d_max = rad.radialDistance.max()
        d_min = rad.radialDistance.min()
        ds = np.arange(d_min, d_max, 0.001)[np.newaxis].T
        ones = np.ones(np.size(ds))[np.newaxis].T
        d = np.concatenate((ds, ones), axis=1)
        x_h = np.squeeze(np.asarray(np.dot(d, self.fit_param[rad_id]["TH"][0])[:, 0]))
        y_h = np.squeeze(np.asarray(np.dot(d, self.fit_param[rad_id]["TH"][1])[:, 0]))
        z_h = np.squeeze(np.asarray(np.dot(d, self.fit_param[rad_id]["TH"][2])[:, 0]))
        fit_table = {"x": x_h, "y": y_h, "z": z_h}
        if var == "3d":
            axes.plot(x_h, y_h, z_h, 'r')
            return
        elif x == "radialDistance":
            if var == "elevation":
                el_h = np.rad2deg(np.arcsin(z_h / np.sqrt(np.power(x_h, 2) + np.power(y_h, 2) + np.power(z_h, 2))))
                axes.plot(ds, el_h, 'r')
            elif var == "azimuth":
                az_h = np.rad2deg(np.arctan(y_h / x_h))
                axes.plot(ds, az_h, 'r')
            elif var in fit_table:
                axes.plot(ds, fit_table[var], 'r')
            else:
                return
        elif x in fit_table:
            if var in fit_table:
                axes.plot(fit_table[x], fit_table[var], 'r')
            else:
                return
        else:
            return
