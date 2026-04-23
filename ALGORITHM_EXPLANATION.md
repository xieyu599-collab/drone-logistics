# 无人机装载核心算法详解

本文档详细解释项目中 `drone_algo.py` 的核心算法实现，包括：

- 这个问题本质上在解决什么
- 为什么要用“贪心初始化 + DFS + 记忆化 + 剪枝”
- 代码里每个函数的职责
- 关键 Python 语法和写法的含义
- 算法运行时每一步到底发生了什么

---

## 1. 问题本质

项目要解决的是一个“多无人机装载优化”问题。

已知：

- 每架无人机都有一个最大载重 `capacities`
- 每个包裹都有一个重量 `packages`
- 每个包裹只能整体装入某一架无人机，不能拆分

目标：

- 让所有无人机装到的包裹总重量尽可能大
- 但每架无人机实际装载重量不能超过它自己的最大载重

这本质上不是简单的单个 0-1 背包，而是：

- 多个“背包”（多架无人机）
- 多个“物品”（多个包裹）
- 每个物品最多选一次
- 每个物品只能放进一个背包

所以它更接近“多背包装载优化问题”。

---

## 2. 核心思想概览

这个实现没有暴力枚举所有可能装法，因为那样会非常慢。它采用了四个策略协同工作：

1. `贪心初始化`
先快速构造一个“还不错”的可行解，作为下界。

2. `DFS 深度优先搜索`
递归尝试每个包裹“装”或“不装”。

3. `记忆化搜索`
把已经算过的状态缓存起来，避免重复计算。

4. `剪枝`
当发现当前分支理论上也不可能超过最优结果时，尽早停止。

这四者组合后，既能保证结果足够优，又能显著降低搜索量。

---

## 3. 文件结构总览

`drone_algo.py` 中最重要的内容有：

- `class DroneLoader`
  算法主体类，封装了装载优化过程和结果
- `greedy_init()`
  先用贪心法给出一个初始可行解
- `_normalize()`
  把状态标准化，方便记忆化缓存
- `_build_process()`
  整理前端和动画需要的过程数据
- `optimize()`
  核心函数，完成最优装载计算
- `show_animation()` 和 `show_final_chart()`
  可视化展示函数
- `parse_int_list()` 和 `main()`
  命令行交互入口

---

## 4. 类属性解释

`DroneLoader` 初始化时定义了 4 个关键属性：

```python
class DroneLoader:
    def __init__(self):
        self.max_total = 0
        self.best_load = []
        self.process = []
        self.best_path = []
```

### 4.1 `self.max_total`

表示当前找到的“最大可装载总重量”。

例如：

- 无人机总共装了 `24`
- 那么 `self.max_total = 24`

### 4.2 `self.best_load`

表示“最优装载方案”里，每架无人机最终装了多少。

例如：

```python
[10, 8, 6]
```

意思是：

- 第 1 架装了 10
- 第 2 架装了 8
- 第 3 架装了 6

### 4.3 `self.process`

表示装载过程，用于前端表格和动画展示。

例如：

```python
[[0, 0, 0], [6, 0, 0], [6, 5, 0]]
```

表示：

- 初始状态全为 0
- 第一步后某架无人机装入了 6
- 第二步后又有一架装入了 5

### 4.4 `self.best_path`

保存最优方案在构造过程中的路径。

和 `self.process` 的区别是：

- `best_path` 通常只保存装载后的连续状态
- `process` 会额外补一个初始全零状态，便于展示

---

## 5. 贪心初始化 `greedy_init`

代码：

```python
def greedy_init(self, packages, capacities):
    drones = [0] * len(capacities)
    remaining = capacities.copy()
    path = []
```

### 5.1 这几行在做什么

#### `drones = [0] * len(capacities)`

创建一个和无人机数量等长的列表，初始值全是 0。

如果有 3 架无人机：

```python
[0, 0, 0]
```

表示当前每架无人机已装载重量都为 0。

#### `remaining = capacities.copy()`

复制一份“剩余容量”。

例如：

```python
capacities = [10, 8, 6]
remaining = [10, 8, 6]
```

之后每装一个包裹，就扣减对应无人机的剩余容量。

#### `path = []`

记录装载过程路径。

---

### 5.2 贪心策略本身

```python
for pkg in packages:
    candidate = -1
    best_remaining = -1
    for i, cap in enumerate(remaining):
        if cap >= pkg and cap > best_remaining:
            best_remaining = cap
            candidate = i
```

这里的含义是：

- 遍历每个包裹 `pkg`
- 在所有“装得下这个包裹”的无人机中
- 找剩余容量最大的那一架

#### `enumerate(remaining)` 是什么

`enumerate()` 会同时给出：

- 下标 `i`
- 对应元素值 `cap`

例如：

```python
for i, cap in enumerate([10, 8, 6]):
```

会依次得到：

- `(0, 10)`
- `(1, 8)`
- `(2, 6)`

#### `candidate = -1`

表示“当前还没找到可装的无人机”。

#### `if cap >= pkg and cap > best_remaining`

这句是双重条件：

- `cap >= pkg`
  当前无人机剩余容量必须能装下这个包裹
- `cap > best_remaining`
  并且它比目前找到的候选无人机剩余容量更大

---

### 5.3 找到目标无人机后如何更新

```python
if candidate != -1:
    remaining[candidate] -= pkg
    drones[candidate] += pkg
    path.append(drones.copy())
```

含义是：

- 如果找到了能装下这个包裹的无人机
- 就从它的剩余容量中减掉包裹重量
- 并把它的当前装载量加上包裹重量
- 然后把当前状态存进路径

#### 为什么这里要 `drones.copy()`

如果直接 `path.append(drones)`，保存的是同一个列表对象的引用；
后面 `drones` 再变化，历史记录也会一起变。

所以必须用 `.copy()` 复制一个快照。

---

### 5.4 贪心初始化的作用

最后：

```python
self.max_total = sum(drones)
self.best_load = drones.copy()
self.best_path = path.copy()
```

这说明：

- 贪心结果先作为当前最优结果
- 即使后面的 DFS 还没跑，我们也已经有一个可行解了

这个可行解的作用非常重要：

- 它给后续搜索提供了“下界”
- 如果某些分支连这个结果都不可能超过，就可以早点放弃

---

## 6. 状态标准化 `_normalize`

代码：

```python
def _normalize(self, remaining):
    return tuple(sorted(remaining, reverse=True))
```

### 6.1 为什么需要标准化

例如两个状态：

```python
(10, 6, 4)
(6, 10, 4)
```

从“剩余容量集合”的角度看，它们本质一样，只是顺序不同。

如果不统一格式：

- 记忆化缓存会把它们当成两个不同状态
- 造成重复搜索

### 6.2 为什么返回 `tuple`

因为 `lru_cache` 要求参数必须是可哈希的。

- `list` 不可哈希
- `tuple` 可哈希

所以这里先排序，再转成元组。

---

## 7. 构建过程数据 `_build_process`

代码：

```python
def _build_process(self):
    self.process = [[0] * len(self.best_load)]
    self.process.extend(self.best_path)
```

含义：

- 先插入一个全 0 的初始状态
- 再把最优路径的每一步追加进去

#### `extend()` 和 `append()` 的区别

`append(x)`：

- 把 `x` 整体当作一个元素加入列表

`extend(x)`：

- 把 `x` 里的每个元素逐个加入列表

这里 `best_path` 本身就是“若干步状态组成的列表”，所以要用 `extend()`。

---

## 8. 核心函数 `optimize`

这是最重要的部分。

---

### 8.1 先排序

```python
packages = sorted(packages, reverse=True)
capacities = sorted(capacities, reverse=True)
```

目的：

- 大包裹优先处理
- 大容量无人机优先考虑

这样通常更容易早一点形成有效装载，也更利于剪枝。

---

### 8.2 重置状态

```python
self.max_total = 0
self.best_load = [0] * len(capacities)
self.process = []
self.best_path = []
```

每次优化前都清空旧结果，避免上一次运行的数据影响本次。

---

### 8.3 计算贪心初值

```python
self.greedy_init(packages, capacities)
```

这一步给搜索提供初始最优方案。

---

### 8.4 构造后缀和 `suffix_sum`

```python
suffix_sum = [0] * (len(packages) + 1)
for i in range(len(packages) - 1, -1, -1):
    suffix_sum[i] = suffix_sum[i + 1] + packages[i]
```

### 8.4.1 它是什么

`suffix_sum[i]` 表示：

- 从第 `i` 个包裹开始
- 到最后所有包裹重量之和

例如：

```python
packages = [6, 5, 4, 3]
suffix_sum = [18, 12, 7, 3, 0]
```

解释：

- `suffix_sum[0] = 6+5+4+3 = 18`
- `suffix_sum[1] = 5+4+3 = 12`
- `suffix_sum[2] = 4+3 = 7`
- `suffix_sum[3] = 3`
- `suffix_sum[4] = 0`

### 8.4.2 为什么有用

后面 DFS 中要计算“理论最大可能收益”，它是剪枝的核心。

---

## 9. 递归核心 `dfs`

代码结构：

```python
@lru_cache(maxsize=None)
def dfs(idx, remaining_state):
```

含义：

- `idx` 表示当前正在处理第几个包裹
- `remaining_state` 表示当前每架无人机剩余容量的标准化状态

函数返回：

```python
(best_extra, best_choice)
```

其中：

- `best_extra`
  从当前状态出发，未来最多还能再装多少重量
- `best_choice`
  达到该最优值时，下一步应该进入哪个状态

---

### 9.1 `@lru_cache(maxsize=None)` 的含义

这是 Python 的记忆化装饰器。

它会自动缓存：

- 相同的 `idx`
- 相同的 `remaining_state`

对应的计算结果。

这样如果递归过程中再次进入相同状态，就不用重新算，直接返回缓存值。

这是性能优化的核心之一。

---

### 9.2 递归终止条件

```python
if idx == len(packages):
    return 0, None
```

表示：

- 如果包裹已经处理完
- 后面就没有额外收益了

所以返回：

- `0`
- `None` 表示没有下一步状态

---

### 9.3 乐观上界 `optimistic`

```python
optimistic = min(suffix_sum[idx], sum(remaining_state))
if optimistic == 0:
    return 0, None
```

这个变量表示：

从当前状态出发，理论上“最多最多”还能装多少。

为什么是：

```python
min(剩余包裹总重, 剩余总容量)
```

因为你未来能增加的总重量，不可能超过这两个值里的较小者：

- 包裹再多，也受容量限制
- 容量再大，也受剩余包裹总重限制

#### 为什么这是“剪枝基础”

如果这个理论上界都很小，那当前状态未来提升空间就有限。

---

### 9.4 当前包裹“不装”的分支

```python
pkg = packages[idx]
best_extra, _ = dfs(idx + 1, remaining_state)
best_choice = None
```

表示：

- 先默认当前包裹不装
- 看看从下一个包裹开始最多能装多少

这相当于先建立一个基线答案。

---

### 9.5 `seen = set()` 的作用

```python
seen = set()
```

后面会遍历每架无人机剩余容量：

```python
for i, cap in enumerate(remaining_state):
    if cap < pkg or cap in seen:
        continue
    seen.add(cap)
```

这里的意思是：

- 如果两架无人机当前剩余容量相同
- 那么把当前包裹放到其中任意一架，得到的状态本质相同

所以：

- 第一架尝试过后
- 第二架相同容量的就没必要重复试

这是一个非常有效的“对称剪枝”。

---

### 9.6 当前包裹“装入某架无人机”的分支

```python
next_remaining = list(remaining_state)
next_remaining[i] -= pkg
next_state = self._normalize(next_remaining)
next_extra, _ = dfs(idx + 1, next_state)
candidate = pkg + next_extra
```

逻辑是：

1. 复制当前剩余容量
2. 把包裹装进第 `i` 架无人机
3. 得到新的剩余容量状态
4. 递归求解后续还能装多少
5. 当前包裹重量 `pkg` 加上后续收益 `next_extra`
6. 得到当前选择的总收益 `candidate`

---

### 9.7 更新当前最优选择

```python
if candidate > best_extra:
    best_extra = candidate
    best_choice = next_state
    if best_extra == optimistic:
        break
```

含义：

- 如果当前方案更优，就更新答案
- `best_choice` 记录最优情况下的下一步状态

#### 为什么 `best_extra == optimistic` 时可以 `break`

因为：

- `optimistic` 已经是理论最大上界
- 你已经达到这个上界了
- 后面再试也不可能更好了

所以可以直接终止本层循环。

这就是非常典型的上界剪枝。

---

### 9.8 DFS 返回值

```python
return best_extra, best_choice
```

返回的不是完整路径，而是：

- 当前状态下能达到的最优收益
- 以及最优时的下一步状态

路径会在后面单独重建。

这样设计的好处是：

- DFS 本身只负责“算值”
- 路径重建逻辑单独处理
- 结构更清晰

---

## 10. 取得最优总重量

```python
best_extra, _ = dfs(0, self._normalize(tuple(capacities)))
self.max_total = max(self.max_total, best_extra)
```

表示从初始状态开始搜索：

- 当前处理第 0 个包裹
- 剩余容量是全部无人机初始容量

最后得到全局最优结果。

这里再和贪心结果比较一次：

- `self.max_total` 里可能已有贪心初值
- `best_extra` 是 DFS 的精确结果
- 用 `max()` 取更优者

---

## 11. 路径重建

DFS 缓存的是“最优值 + 下一状态”，不是完整装载路径，所以需要后处理重建。

代码：

```python
loads = [0] * len(capacities)
path = []
idx = 0
state = self._normalize(tuple(capacities))
```

这些变量含义：

- `loads`
  当前已经装到每架无人机上的重量
- `path`
  记录过程
- `idx`
  当前处理到第几个包裹
- `state`
  当前剩余容量状态

---

### 11.1 重建主循环

```python
while idx < len(packages):
    pkg = packages[idx]
    _, next_state = dfs(idx, state)
    if next_state is None:
        idx += 1
        continue
```

含义：

- 看当前状态下，最优决策给出的下一状态是什么
- 如果 `next_state is None`
  说明当前包裹在最优解里没有装
- 就跳到下一个包裹

---

### 11.2 确认包裹装到了哪架无人机

```python
current_list = list(state)
next_list = list(next_state)

for i in range(len(current_list)):
    if current_list[i] - next_list[i] == pkg:
        loads[i] += pkg
        path.append(loads.copy())
        break
```

思路是：

- 比较当前状态和下一状态
- 哪一位剩余容量恰好减少了 `pkg`
- 就说明该包裹装进了哪架无人机

然后：

- 更新该无人机的已装载量
- 保存当前装载快照

---

### 11.3 为什么这样能恢复路径

因为 DFS 中记录的是“下一状态”。

如果：

```python
state = (10, 8, 6)
next_state = (8, 8, 6)
pkg = 2
```

那就说明：

- 第一架无人机从 10 变 8
- 这个包裹装到了第一架上

---

## 12. 最终结果写回对象

```python
if sum(loads) >= sum(self.best_load):
    self.best_load = loads
    self.best_path = path

self._build_process()
```

这一步表示：

- 如果 DFS 重建出的方案不比当前记录差
- 就用它更新最优方案

最后调用 `_build_process()` 生成完整过程数据。

---

## 13. 一个具体例子

假设：

```python
capacities = [10, 8, 6]
packages = [6, 5, 4, 4, 3, 2]
```

排序后不变。

### 13.1 贪心初始化可能得到

- 6 放到 10
- 5 放到 8
- 4 放到剩余最大位置
- ...

可能先得到一个可行方案，例如：

```python
best_load = [10, 8, 6]
max_total = 24
```

### 13.2 DFS 再检查

DFS 会系统判断：

- 某些包裹不装会不会更优
- 某个包裹换到别的无人机上会不会更优
- 某些状态是不是已经计算过

如果发现贪心已经是最优，就保持不变；
如果发现存在更好的分配，就替换。

---

## 14. 时间复杂度与性能来源

严格说，这类问题仍然属于组合优化问题，最坏情况下搜索空间很大。

但这份代码通过几个手段显著压缩了实际搜索量：

1. 包裹按降序处理
大包裹优先，有利于更早产生明显分支差异。

2. 状态标准化
把顺序不同但本质相同的状态合并。

3. `lru_cache`
同一状态只算一次。

4. `seen` 去重
相同剩余容量的无人机不重复尝试。

5. 上界剪枝
达到理论最优后立即终止分支。

因此在当前项目设定范围内：

- 最多 5 架无人机
- 最多 50 个包裹

整体是可用的。

---

## 15. 关键 Python 语法解释

这一部分专门解释代码中容易“看懂大意，但不确定语法”的地方。

### 15.1 `list.copy()`

```python
remaining = capacities.copy()
```

表示复制一个新列表。

如果不用 `copy()`，两个变量可能引用同一块列表对象，改一个会影响另一个。

---

### 15.2 `sorted(..., reverse=True)`

```python
sorted(packages, reverse=True)
```

表示按降序排序。

---

### 15.3 `tuple(...)`

把列表转换成元组，常用于：

- 不希望被修改
- 需要作为字典键或缓存键

---

### 15.4 `@lru_cache(maxsize=None)`

函数装饰器。

作用：

- 自动缓存函数输入和输出
- 再次调用相同参数时直接返回历史结果

---

### 15.5 内部函数

```python
def optimize(...):
    @lru_cache(maxsize=None)
    def dfs(idx, remaining_state):
        ...
```

这里的 `dfs` 是定义在 `optimize` 里面的“内部函数”。

好处：

- 它只在本次优化时有效
- 能直接访问 `packages`、`suffix_sum` 等外层变量

这是一种很常见的 Python 闭包写法。

---

### 15.6 `continue` 和 `break`

`continue`：

- 跳过本轮循环，进入下一轮

`break`：

- 直接结束整个循环

例如：

```python
if cap < pkg or cap in seen:
    continue
```

表示当前这个候选无人机不合适，跳过它。

而：

```python
if best_extra == optimistic:
    break
```

表示本层已经不可能更优了，直接停止遍历。

---

## 16. 可视化函数的角色

### 16.1 `show_animation`

使用 `matplotlib.animation.FuncAnimation` 展示装载过程的动态柱状图。

它不参与求解，只负责展示 `self.process`。

### 16.2 `show_final_chart`

生成 4 个子图：

- 包裹重量分布
- 无人机最大载重
- 最优装载方案
- 文本总结

这部分也不参与求解，只是把计算结果展示出来。

---

## 17. 命令行入口和 Web 接口如何调用算法

### 17.1 命令行方式

`main()` 中会：

1. 读取用户输入
2. 解析整数列表
3. 校验数量是否匹配
4. 调用 `loader.optimize(packages, capacities)`
5. 输出结果并展示图表

### 17.2 FastAPI 方式

`backend/main.py` 中：

```python
loader = DroneLoader()
loader.optimize(request.packages, request.capacities)
```

说明后端接口只是把前端传来的数据交给算法类处理，再把结果封装为 JSON 返回。

也就是说：

- 真正的核心算法仍然在 `drone_algo.py`
- FastAPI 只是“输入输出包装层”

---

## 18. 为什么这份实现值得保留

这份实现的优点在于：

1. 结构清晰
求解、路径记录、可视化、接口调用是分开的。

2. 优化思路合理
不是单纯暴力搜索，而是用了多种剪枝和缓存技巧。

3. 易于扩展
后续如果要增加：

- 包裹优先级
- 无人机类型
- 禁飞限制
- 多目标优化

都可以继续在这个框架上扩展。

---

## 19. 一句话总结

这套算法可以概括为：

> 先用贪心快速找到一个可行装载方案，再用带记忆化和剪枝的深度优先搜索，在“剩余容量状态空间”中寻找总装载重量最大的最优解，最后重建装载路径并输出给前端展示。

如果你还需要，我下一步可以继续帮你补一版：

- “适合答辩/汇报”的算法说明版
- 或者“带流程图”的教学版文档
