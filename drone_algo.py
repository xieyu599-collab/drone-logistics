import re
from functools import lru_cache


class DroneLoader:
    def __init__(self):
        self.max_total = 0
        self.best_load = []
        self.process = []
        self.best_path = []

    def greedy_init(self, packages, capacities):
        """Best Fit Decreasing: 选能装下且剩余容量最小的无人机，给出更紧的下界。"""
        drones = [0] * len(capacities)
        remaining = capacities.copy()
        path = []

        for pkg in packages:
            candidate = -1
            best_remaining = float('inf')
            for i, cap in enumerate(remaining):
                if cap >= pkg and cap < best_remaining:
                    best_remaining = cap
                    candidate = i

            if candidate != -1:
                remaining[candidate] -= pkg
                drones[candidate] += pkg
                path.append(drones.copy())

        self.max_total = sum(drones)
        self.best_load = drones.copy()
        self.best_path = path.copy()

    def _normalize(self, remaining):
        return tuple(sorted(remaining, reverse=True))

    def _build_process(self):
        self.process = [[0] * len(self.best_load)]
        self.process.extend(self.best_path)

    def optimize(self, packages, capacities):
        packages = sorted(packages, reverse=True)
        capacities = sorted(capacities, reverse=True)

        self.max_total = 0
        self.best_load = [0] * len(capacities)
        self.process = []
        self.best_path = []

        self.greedy_init(packages, capacities)
        suffix_sum = [0] * (len(packages) + 1)
        for i in range(len(packages) - 1, -1, -1):
            suffix_sum[i] = suffix_sum[i + 1] + packages[i]

        theoretical_max = min(suffix_sum[0], sum(capacities))
        if self.max_total >= theoretical_max:
            self._build_process()
            return

        @lru_cache(maxsize=None)
        def dfs(idx, remaining_state):
            if idx == len(packages):
                return 0, None

            total_remaining = sum(remaining_state)
            optimistic = min(suffix_sum[idx], total_remaining)
            if optimistic == 0:
                return 0, None

            pkg = packages[idx]

            if pkg > remaining_state[0]:
                val, _ = dfs(idx + 1, remaining_state)
                return val, None

            best_extra, _ = dfs(idx + 1, remaining_state)
            best_choice = None
            seen = set()

            for i in range(len(remaining_state) - 1, -1, -1):
                cap = remaining_state[i]
                if cap < pkg or cap in seen:
                    continue
                seen.add(cap)

                next_remaining = list(remaining_state)
                next_remaining[i] -= pkg
                next_state = self._normalize(next_remaining)
                next_extra, _ = dfs(idx + 1, next_state)
                candidate = pkg + next_extra

                if candidate > best_extra:
                    best_extra = candidate
                    best_choice = next_state
                    if best_extra == optimistic:
                        break

            return best_extra, best_choice

        best_extra, _ = dfs(0, self._normalize(tuple(capacities)))
        self.max_total = max(self.max_total, best_extra)

        loads = [0] * len(capacities)
        path = []
        idx = 0
        state = self._normalize(tuple(capacities))

        while idx < len(packages):
            pkg = packages[idx]
            _, next_state = dfs(idx, state)
            if next_state is None:
                idx += 1
                continue

            current_list = list(state)
            next_list = list(next_state)

            for i in range(len(current_list)):
                if current_list[i] - next_list[i] == pkg:
                    loads[i] += pkg
                    path.append(loads.copy())
                    break

            state = next_state
            idx += 1

        if sum(loads) >= sum(self.best_load):
            self.best_load = loads
            self.best_path = path

        self._build_process()

    def show_animation(self, capacities):
        import matplotlib.animation as animation
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_title("无人机装载动态流程", fontsize=14)
        ax.set_ylabel("当前装载重量")
        ax.set_ylim(0, max(capacities) + 5)

        bars = ax.bar(
            [f"无人机{i + 1}" for i in range(len(capacities))],
            [0] * len(capacities),
            color=["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2"],
        )

        for i, cap in enumerate(capacities):
            ax.axhline(
                y=cap,
                xmin=i / len(capacities) + 0.05,
                xmax=(i + 1) / len(capacities) - 0.05,
                color="#C62828",
                linestyle="--",
                linewidth=2,
            )

        def update(frame):
            for i, bar in enumerate(bars):
                bar.set_height(frame[i])
            return bars

        animation.FuncAnimation(fig, update, frames=self.process, interval=300, blit=True)
        plt.tight_layout()
        plt.show()

    def show_final_chart(self, capacities, packages):
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei"]
        plt.rcParams["axes.unicode_minus"] = False
        plt.figure(figsize=(12, 8))

        plt.subplot(2, 2, 1)
        plt.bar(range(1, len(packages) + 1), packages, color="#A0CBE8")
        plt.title("包裹重量分布")
        plt.xlabel("包裹编号")

        plt.subplot(2, 2, 2)
        plt.bar([f"无人机{i + 1}" for i in range(len(capacities))], capacities, color="#F28E2B")
        plt.title("无人机最大载重上限")

        plt.subplot(2, 2, 3)
        plt.bar(
            [f"无人机{i + 1}" for i in range(len(capacities))],
            self.best_load,
            color=["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2"],
        )
        for i, cap in enumerate(capacities):
            plt.axhline(
                cap,
                i / len(capacities) + 0.05,
                (i + 1) / len(capacities) - 0.05,
                color="#C62828",
                linestyle="--",
                linewidth=2,
            )
        plt.title("最优装载方案")

        plt.subplot(2, 2, 4)
        plt.text(0.5, 0.7, f"最大总重量：{self.max_total}", fontsize=14, ha="center")
        plt.text(0.5, 0.4, f"无人机：{len(capacities)} 架，包裹：{len(packages)} 个", fontsize=12, ha="center")
        plt.axis("off")

        plt.tight_layout()
        plt.show()


def parse_int_list(text):
    parts = re.split(r"[\s,，]+", text.strip())
    return [int(x) for x in parts if x]


def main():
    loader = DroneLoader()

    print("请输入：无人机数量m 包裹数量n")
    m, n = parse_int_list(input())
    print("请输入：每架无人机最大载重")
    capacities = parse_int_list(input())
    print("请输入：每个包裹重量")
    packages = parse_int_list(input())

    if len(capacities) != m:
        raise ValueError(f"需要输入 {m} 个无人机载重，但实际输入了 {len(capacities)} 个")
    if len(packages) != n:
        raise ValueError(f"需要输入 {n} 个包裹重量，但实际输入了 {len(packages)} 个")

    loader.optimize(packages, capacities)

    print("=" * 40)
    print("最大可装载重量：", loader.max_total)
    print("最优装载方案：", loader.best_load)
    print("=" * 40)

    loader.show_final_chart(capacities, packages)
    loader.show_animation(capacities)


if __name__ == "__main__":
    main()
