# drone_algo.py 代码详细分析

## 1. 导入模块

```python
import re
from functools import lru_cache
```
- **`import re`**：导入正则表达式模块，用于字符串处理。
- **`from functools import lru_cache`**：从functools模块导入lru_cache装饰器，用于缓存函数结果，提高递归函数的性能。

## 2. 类定义与初始化

```python
class DroneLoader:
    def __init__(self):
        self.max_total = 0
        self.best_load = []
        self.process = []
        self.best_path = []
```
- **`class DroneLoader:`**：定义DroneLoader类，用于处理无人机装载优化问题。
- **`def __init__(self):`**：初始化方法，创建对象时自动调用。
- **`self.max_total = 0`**：初始化最大总装载重量为0。
- **`self.best_load = []`**：初始化最优装载方案为空列表。
- **`self.process = []`**：初始化装载过程为空列表。
- **`self.best_path = []`**：初始化最优路径为空列表。

## 3. 贪心初始化方法

```python
def greedy_init(self, packages, capacities):
    """贪心给出一个可行下界，帮助后续剪枝。"""
    drones = [0] * len(capacities)
    remaining = capacities.copy()
    path = []

    for pkg in packages:
        candidate = -1
        best_remaining = -1
        for i, cap in enumerate(remaining):
            if cap >= pkg and cap > best_remaining:
                best_remaining = cap
                candidate = i

        if candidate != -1:
            remaining[candidate] -= pkg
            drones[candidate] += pkg
            path.append(drones.copy())

    self.max_total = sum(drones)
    self.best_load = drones.copy()
    self.best_path = path.copy()
```
- **`def greedy_init(self, packages, capacities):`**：定义贪心初始化方法，参数为包裹重量列表和无人机载重列表。
- **`"""贪心给出一个可行下界，帮助后续剪枝。"""`**：文档字符串，说明该方法的作用。
- **`drones = [0] * len(capacities)`**：初始化无人机装载重量列表，所有无人机初始装载为0。
- **`remaining = capacities.copy()`**：复制无人机载重列表，用于记录剩余载重。
- **`path = []`**：初始化路径列表，用于记录装载过程。
- **`for pkg in packages:`**：遍历每个包裹。
- **`candidate = -1`**：初始化候选无人机索引为-1。
- **`best_remaining = -1`**：初始化最佳剩余载重为-1。
- **`for i, cap in enumerate(remaining):`**：遍历每个无人机的剩余载重。
- **`if cap >= pkg and cap > best_remaining:`**：如果无人机剩余载重大于等于包裹重量，且大于当前最佳剩余载重。
- **`best_remaining = cap`**：更新最佳剩余载重。
- **`candidate = i`**：更新候选无人机索引。
- **`if candidate != -1:`**：如果找到合适的无人机。
- **`remaining[candidate] -= pkg`**：减少对应无人机的剩余载重。
- **`drones[candidate] += pkg`**：增加对应无人机的装载重量。
- **`path.append(drones.copy())`**：记录当前装载状态。
- **`self.max_total = sum(drones)`**：计算并保存最大总装载重量。
- **`self.best_load = drones.copy()`**：保存最优装载方案。
- **`self.best_path = path.copy()`**：保存最优路径。

## 4. 辅助方法

### 4.1 状态归一化方法

```python
def _normalize(self, remaining):
    return tuple(sorted(remaining, reverse=True))
```
- **`def _normalize(self, remaining):`**：定义状态归一化方法，参数为剩余载重列表。
- **`return tuple(sorted(remaining, reverse=True))`**：将剩余载重列表按降序排序并转换为元组，用于状态缓存。

### 4.2 构建过程方法

```python
def _build_process(self):
    self.process = [[0] * len(self.best_load)]
    self.process.extend(self.best_path)
```
- **`def _build_process(self):`**：定义构建过程方法，用于构建装载过程。
- **`self.process = [[0] * len(self.best_load)]`**：初始化过程列表，第一个元素为全0的装载状态。
- **`self.process.extend(self.best_path)`**：将最优路径添加到过程列表中。

## 5. 核心优化方法

```python
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

    @lru_cache(maxsize=None)
    def dfs(idx, remaining_state):
        if idx == len(packages):
            return 0, None

        optimistic = min(suffix_sum[idx], sum(remaining_state))
        if optimistic == 0:
            return 0, None

        pkg = packages[idx]
        best_extra, _ = dfs(idx + 1, remaining_state)
        best_choice = None
        seen = set()

        for i, cap in enumerate(remaining_state):
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
```
- **`def optimize(self, packages, capacities):`**：定义核心优化方法，参数为包裹重量列表和无人机载重列表。
- **`packages = sorted(packages, reverse=True)`**：将包裹按重量降序排序。
- **`capacities = sorted(capacities, reverse=True)`**：将无人机载重按降序排序。
- **`self.max_total = 0`**：重置最大总装载重量为0。
- **`self.best_load = [0] * len(capacities)`**：重置最优装载方案。
- **`self.process = []`**：重置过程列表。
- **`self.best_path = []`**：重置最优路径。
- **`self.greedy_init(packages, capacities)`**：调用贪心初始化方法，获取初始可行解。
- **`suffix_sum = [0] * (len(packages) + 1)`**：初始化后缀和数组，用于剪枝。
- **`for i in range(len(packages) - 1, -1, -1):`**：从后向前计算后缀和。
- **`suffix_sum[i] = suffix_sum[i + 1] + packages[i]`**：计算从当前包裹到最后一个包裹的重量和。
- **`@lru_cache(maxsize=None)`**：使用lru_cache装饰器缓存dfs函数结果，提高性能。
- **`def dfs(idx, remaining_state):`**：定义深度优先搜索函数，参数为当前包裹索引和剩余载重状态。
- **`if idx == len(packages):`**：如果所有包裹都已处理完毕。
- **`return 0, None`**：返回0和None，表示没有更多包裹可装。
- **`optimistic = min(suffix_sum[idx], sum(remaining_state))`**：计算乐观估计值，即剩余包裹重量和与剩余载重的最小值。
- **`if optimistic == 0:`**：如果乐观估计值为0。
- **`return 0, None`**：返回0和None，表示无法再装载更多包裹。
- **`pkg = packages[idx]`**：获取当前包裹重量。
- **`best_extra, _ = dfs(idx + 1, remaining_state)`**：递归处理下一个包裹，不装当前包裹。
- **`best_choice = None`**：初始化最佳选择为None。
- **`seen = set()`**：初始化已处理的载重集合，用于去重。
- **`for i, cap in enumerate(remaining_state):`**：遍历每个无人机的剩余载重。
- **`if cap < pkg or cap in seen:`**：如果剩余载重小于包裹重量或已处理过相同载重。
- **`continue`**：跳过当前循环。
- **`seen.add(cap)`**：将当前载重添加到已处理集合。
- **`next_remaining = list(remaining_state)`**：复制剩余载重状态。
- **`next_remaining[i] -= pkg`**：减少对应无人机的剩余载重。
- **`next_state = self._normalize(next_remaining)`**：归一化下一个状态。
- **`next_extra, _ = dfs(idx + 1, next_state)`**：递归处理下一个包裹，装当前包裹。
- **`candidate = pkg + next_extra`**：计算当前选择的总装载重量。
- **`if candidate > best_extra:`**：如果当前选择更优。
- **`best_extra = candidate`**：更新最佳额外装载重量。
- **`best_choice = next_state`**：更新最佳选择状态。
- **`if best_extra == optimistic:`**：如果已达到乐观估计值。
- **`break`**：提前终止循环。
- **`return best_extra, best_choice`**：返回最佳额外装载重量和最佳选择状态。
- **`best_extra, _ = dfs(0, self._normalize(tuple(capacities)))`**：调用dfs函数，从第一个包裹开始，初始状态为归一化后的载重。
- **`self.max_total = max(self.max_total, best_extra)`**：更新最大总装载重量。
- **`loads = [0] * len(capacities)`**：初始化装载重量列表。
- **`path = []`**：初始化路径列表。
- **`idx = 0`**：初始化包裹索引为0。
- **`state = self._normalize(tuple(capacities))`**：初始化状态为归一化后的载重。
- **`while idx < len(packages):`**：遍历所有包裹。
- **`pkg = packages[idx]`**：获取当前包裹重量。
- **`_, next_state = dfs(idx, state)`**：调用dfs函数，获取下一个状态。
- **`if next_state is None:`**：如果没有找到合适的装载位置。
- **`idx += 1`**：处理下一个包裹。
- **`continue`**：跳过当前循环。
- **`current_list = list(state)`**：将当前状态转换为列表。
- **`next_list = list(next_state)`**：将下一个状态转换为列表。
- **`for i in range(len(current_list)):`**：遍历每个无人机。
- **`if current_list[i] - next_list[i] == pkg:`**：如果当前无人机的载重减少量等于包裹重量。
- **`loads[i] += pkg`**：增加对应无人机的装载重量。
- **`path.append(loads.copy())`**：记录当前装载状态。
- **`break`**：终止循环。
- **`state = next_state`**：更新状态为下一个状态。
- **`idx += 1`**：处理下一个包裹。
- **`if sum(loads) >= sum(self.best_load):`**：如果当前装载方案优于或等于之前的最优方案。
- **`self.best_load = loads`**：更新最优装载方案。
- **`self.best_path = path`**：更新最优路径。
- **`self._build_process()`**：构建装载过程。

## 6. 可视化方法

### 6.1 动态动画展示

```python
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
```
- **`def show_animation(self, capacities):`**：定义动态动画展示方法，参数为无人机载重列表。
- **`import matplotlib.animation as animation`**：导入matplotlib动画模块。
- **`import matplotlib.pyplot as plt`**：导入matplotlib绘图模块。
- **`plt.rcParams["font.sans-serif"] = ["SimHei"]`**：设置中文字体为SimHei。
- **`plt.rcParams["axes.unicode_minus"] = False`**：解决负号显示问题。
- **`fig, ax = plt.subplots(figsize=(8, 5))`**：创建图形和坐标轴。
- **`ax.set_title("无人机装载动态流程", fontsize=14)`**：设置标题。
- **`ax.set_ylabel("当前装载重量")`**：设置y轴标签。
- **`ax.set_ylim(0, max(capacities) + 5)`**：设置y轴范围。
- **`bars = ax.bar([f"无人机{i + 1}" for i in range(len(capacities))], [0] * len(capacities), color=["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2"])`**：创建初始柱状图。
- **`for i, cap in enumerate(capacities):`**：遍历每个无人机的载重。
- **`ax.axhline(y=cap, xmin=i / len(capacities) + 0.05, xmax=(i + 1) / len(capacities) - 0.05, color="#C62828", linestyle="--", linewidth=2)`**：绘制无人机载重上限的虚线。
- **`def update(frame):`**：定义更新函数，用于动画。
- **`for i, bar in enumerate(bars):`**：遍历每个柱状图。
- **`bar.set_height(frame[i])`**：更新柱状图高度。
- **`return bars`**：返回更新后的柱状图。
- **`animation.FuncAnimation(fig, update, frames=self.process, interval=300, blit=True)`**：创建动画，使用process作为帧，间隔300毫秒。
- **`plt.tight_layout()`**：调整布局。
- **`plt.show()`**：显示动画。

### 6.2 最终结果图表

```python
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
```
- **`def show_final_chart(self, capacities, packages):`**：定义最终结果图表展示方法，参数为无人机载重列表和包裹重量列表。
- **`import matplotlib.pyplot as plt`**：导入matplotlib绘图模块。
- **`plt.rcParams["font.sans-serif"] = ["SimHei"]`**：设置中文字体为SimHei。
- **`plt.rcParams["axes.unicode_minus"] = False`**：解决负号显示问题。
- **`plt.figure(figsize=(12, 8))`**：创建图形，设置大小。
- **`plt.subplot(2, 2, 1)`**：创建第一个子图，2行2列的第1个位置。
- **`plt.bar(range(1, len(packages) + 1), packages, color="#A0CBE8")`**：绘制包裹重量分布柱状图。
- **`plt.title("包裹重量分布")`**：设置标题。
- **`plt.xlabel("包裹编号")`**：设置x轴标签。
- **`plt.subplot(2, 2, 2)`**：创建第二个子图，2行2列的第2个位置。
- **`plt.bar([f"无人机{i + 1}" for i in range(len(capacities))], capacities, color="#F28E2B")`**：绘制无人机最大载重上限柱状图。
- **`plt.title("无人机最大载重上限")`**：设置标题。
- **`plt.subplot(2, 2, 3)`**：创建第三个子图，2行2列的第3个位置。
- **`plt.bar([f"无人机{i + 1}" for i in range(len(capacities))], self.best_load, color=["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2"])`**：绘制最优装载方案柱状图。
- **`for i, cap in enumerate(capacities):`**：遍历每个无人机的载重。
- **`plt.axhline(cap, i / len(capacities) + 0.05, (i + 1) / len(capacities) - 0.05, color="#C62828", linestyle="--", linewidth=2)`**：绘制无人机载重上限的虚线。
- **`plt.title("最优装载方案")`**：设置标题。
- **`plt.subplot(2, 2, 4)`**：创建第四个子图，2行2列的第4个位置。
- **`plt.text(0.5, 0.7, f"最大总重量：{self.max_total}", fontsize=14, ha="center")`**：添加最大总重量文本。
- **`plt.text(0.5, 0.4, f"无人机：{len(capacities)} 架，包裹：{len(packages)} 个", fontsize=12, ha="center")`**：添加无人机和包裹数量文本。
- **`plt.axis("off")`**：关闭坐标轴。
- **`plt.tight_layout()`**：调整布局。
- **`plt.show()`**：显示图表。

## 7. 辅助函数

```python
def parse_int_list(text):
    parts = re.split(r"[\s,，]+", text.strip())
    return [int(x) for x in parts if x]
```
- **`def parse_int_list(text):`**：定义解析整数列表的函数，参数为文本字符串。
- **`parts = re.split(r"[\s,，]+", text.strip())`**：使用正则表达式分割文本，支持空格、英文逗号和中文逗号。
- **`return [int(x) for x in parts if x]`**：将非空部分转换为整数并返回列表。

## 8. 主函数

```python
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
```
- **`def main():`**：定义主函数。
- **`loader = DroneLoader()`**：创建DroneLoader对象。
- **`print("请输入：无人机数量m 包裹数量n")`**：提示用户输入无人机数量和包裹数量。
- **`m, n = parse_int_list(input())`**：解析用户输入的无人机数量和包裹数量。
- **`print("请输入：每架无人机最大载重")`**：提示用户输入每架无人机的最大载重。
- **`capacities = parse_int_list(input())`**：解析用户输入的无人机载重列表。
- **`print("请输入：每个包裹重量")`**：提示用户输入每个包裹的重量。
- **`packages = parse_int_list(input())`**：解析用户输入的包裹重量列表。
- **`if len(capacities) != m:`**：检查无人机载重数量是否与输入的无人机数量一致。
- **`raise ValueError(f"需要输入 {m} 个无人机载重，但实际输入了 {len(capacities)} 个")`**：如果不一致，抛出 ValueError 异常。
- **`if len(packages) != n:`**：检查包裹重量数量是否与输入的包裹数量一致。
- **`raise ValueError(f"需要输入 {n} 个包裹重量，但实际输入了 {len(packages)} 个")`**：如果不一致，抛出 ValueError 异常。
- **`loader.optimize(packages, capacities)`**：调用优化方法，计算最优装载方案。
- **`print("=" * 40)`**：打印分隔线。
- **`print("最大可装载重量：", loader.max_total)`**：打印最大可装载重量。
- **`print("最优装载方案：", loader.best_load)`**：打印最优装载方案。
- **`print("=" * 40)`**：打印分隔线。
- **`loader.show_final_chart(capacities, packages)`**：显示最终结果图表。
- **`loader.show_animation(capacities)`**：显示动态动画。

## 9. 主入口判断

```python
if __name__ == "__main__":
    main()
```
- **`if __name__ == "__main__":`**：判断当前模块是否作为主模块运行。
- **`main()`**：如果是主模块，调用主函数。

## 代码整体分析

### 核心算法

1. **贪心初始化**：使用贪心算法快速获取一个可行的初始解，作为后续优化的下界。
2. **深度优先搜索(DFS)**：结合记忆化缓存，搜索所有可能的装载方案，寻找最优解。
3. **剪枝策略**：使用后缀和计算乐观估计值，提前终止不可能产生更优解的搜索路径。
4. **状态归一化**：通过排序将相同载重分布的不同排列视为同一状态，减少搜索空间。

### 优化策略

1. **排序优化**：将包裹和无人机载重按降序排序，优先处理重量较大的包裹，提高剪枝效率。
2. **记忆化缓存**：使用lru_cache装饰器缓存DFS函数的结果，避免重复计算。
3. **状态去重**：使用集合记录已处理的载重值，避免对相同载重的无人机进行重复处理。
4. **提前终止**：当达到乐观估计值时，提前终止搜索，减少计算量。

### 可视化功能

1. **动态动画**：通过matplotlib的动画功能，展示无人机装载的动态过程。
2. **结果图表**：使用matplotlib绘制包裹重量分布、无人机载重上限和最优装载方案的图表，直观展示优化结果。

### 输入输出处理

1. **输入解析**：使用正则表达式解析用户输入，支持空格、英文逗号和中文逗号分隔的数字列表。
2. **错误处理**：检查输入的无人机数量和包裹数量是否与实际输入的列表长度一致，不一致时抛出异常。
3. **结果输出**：打印最大可装载重量和最优装载方案，并通过图表和动画展示结果。

### 代码结构

1. **类结构**：使用DroneLoader类封装所有相关功能，包括初始化、优化、可视化等方法。
2. **模块化设计**：将不同功能拆分为独立的方法，如贪心初始化、DFS搜索、状态归一化、可视化等。
3. **辅助函数**：将输入解析等通用功能提取为独立的辅助函数，提高代码复用性。
4. **主函数**：提供命令行交互界面，方便用户输入参数并查看结果。

### 性能考虑

1. **时间复杂度**：DFS搜索的时间复杂度为O(n * m^n)，其中n是包裹数量，m是无人机数量。但通过剪枝和记忆化缓存，实际运行时间会大大减少。
2. **空间复杂度**：记忆化缓存的空间复杂度取决于不同状态的数量，最坏情况下为O(m^n)。
3. **输入规模**：由于DFS的时间复杂度较高，该算法适用于包裹数量较少的场景（如代码中提到的最多50个包裹）。

### 代码优化建议

1. **并行计算**：对于大规模问题，可以考虑使用并行计算来加速DFS搜索。
2. **启发式算法**：对于更大规模的问题，可以考虑使用遗传算法、模拟退火等启发式算法，在合理时间内找到近似最优解。
3. **输入验证**：增加对输入值的范围验证，确保输入的重量值为正整数，避免无效输入导致的错误。
4. **异常处理**：增加更全面的异常处理，提高代码的健壮性。
5. **代码注释**：增加更多的代码注释，特别是对复杂算法部分的解释，提高代码的可读性。

## 总结

drone_algo.py实现了一个无人机装载优化系统，使用贪心算法和深度优先搜索结合剪枝策略，寻找最优的包裹装载方案。该系统具有以下特点：

1. **高效算法**：结合贪心初始化和深度优先搜索，在保证找到最优解的同时，通过剪枝和记忆化缓存提高搜索效率。
2. **直观可视化**：通过动态动画和结果图表，直观展示装载过程和优化结果。
3. **用户友好**：提供命令行交互界面，支持多种输入格式，方便用户使用。
4. **模块化设计**：代码结构清晰，功能模块化，便于维护和扩展。

该系统可以应用于实际的无人机物流配送场景，帮助优化包裹装载方案，提高配送效率。