<script setup>
import { computed, reactive, ref } from "vue";

const defaults = {
  capacities: "10, 8, 6",
  packages: "6, 5, 4, 4, 3, 2",
};

const form = reactive({
  capacities: defaults.capacities,
  packages: defaults.packages,
});

const loading = ref(false);
const error = ref("");
const result = ref(null);

const badges = ["包裹不可拆分", "多机协同装载", "最优重量求解", "装载过程追踪"];
const systemHighlights = [
  { label: "算法核心", value: "0-1 背包 + DFS" },
  { label: "输入规模", value: "最多 5 架 / 50 件" },
  { label: "返回结果", value: "总量、明细、过程" },
];
const statMeta = [
  { key: "max_total", label: "最大可装载重量", note: "当前最优组合总重量" },
  { key: "total_capacity", label: "无人机总载重上限", note: "全部无人机理论极限" },
  { key: "utilization", label: "整体利用率", note: "实际装载 / 总载重上限" },
  { key: "undelivered", label: "未配送重量", note: "总包裹重量 - 已装载重量" },
];

const parseNumbers = (text) =>
  text
    .split(/[\s,，]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => Number(item));

const packageBars = computed(() => {
  if (!result.value) return [];
  const values = [...result.value.packages].sort((a, b) => b - a);
  const max = Math.max(...values, 1);
  return values.map((value, index) => ({
    label: `包裹${index + 1}`,
    value,
    ratio: (value / max) * 100,
  }));
});

const loadBars = computed(() => {
  if (!result.value) return [];
  const max = Math.max(...result.value.capacities, 1);
  return result.value.capacities.map((capacity, index) => ({
    label: `无人机${index + 1}`,
    capacity,
    load: result.value.best_load[index],
    capacityRatio: (capacity / max) * 100,
    loadRatio: (result.value.best_load[index] / max) * 100,
  }));
});

const processRows = computed(() => {
  if (!result.value) return [];
  return result.value.process.map((loads, index) => ({
    step: index,
    total: loads.reduce((sum, value) => sum + value, 0),
    loads,
  }));
});

const packageSummary = computed(() => {
  const values = parseNumbers(form.packages).filter((value) => Number.isFinite(value) && value > 0);
  return {
    count: values.length,
    total: values.reduce((sum, value) => sum + value, 0),
  };
});

const capacitySummary = computed(() => {
  const values = parseNumbers(form.capacities).filter((value) => Number.isFinite(value) && value > 0);
  return {
    count: values.length,
    total: values.reduce((sum, value) => sum + value, 0),
  };
});

const dashboardStats = computed(() => {
  if (!result.value) return [];

  return statMeta.map((item) => {
    const rawValue = result.value[item.key];
    const displayValue = item.key === "utilization" ? `${(rawValue * 100).toFixed(1)}%` : rawValue;

    return {
      ...item,
      value: displayValue,
    };
  });
});

const fillExample = () => {
  form.capacities = "12, 10, 8, 6";
  form.packages = "7, 6, 5, 4, 4, 3, 2, 2";
};

const resetForm = () => {
  form.capacities = defaults.capacities;
  form.packages = defaults.packages;
  error.value = "";
};

const optimize = async () => {
  error.value = "";

  const capacities = parseNumbers(form.capacities);
  const packages = parseNumbers(form.packages);

  if (!capacities.length || !packages.length || [...capacities, ...packages].some((value) => !Number.isInteger(value) || value <= 0)) {
    error.value = "请输入正整数，支持空格、英文逗号、中文逗号分隔。";
    return;
  }

  loading.value = true;

  try {
    const response = await fetch("/api/optimize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ capacities, packages }),
    });

    const rawText = await response.text();
    const payload = rawText ? JSON.parse(rawText) : null;

    if (!response.ok) {
      throw new Error(payload?.detail || "优化请求失败");
    }

    if (!payload) {
      throw new Error("后端服务未返回有效数据");
    }

    result.value = payload;
  } catch (requestError) {
    if (requestError instanceof SyntaxError) {
      error.value = "后端返回的不是有效 JSON，请确认后端服务已正常启动。";
      return;
    }

    error.value = requestError.message || "无法连接后端服务";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="page-shell">
    <aside class="sidebar-card">
      <div class="sidebar-intro">
        <p class="eyebrow">智能装载分析</p>
        <h2>输入参数</h2>
        <p class="muted">支持空格、英文逗号、中文逗号分隔。系统会自动校验输入并生成最优装载结果。</p>
      </div>

      <div class="quick-stats">
        <article class="quick-stat">
          <span>无人机数量</span>
          <strong>{{ capacitySummary.count }}</strong>
          <small>总载重 {{ capacitySummary.total }}</small>
        </article>
        <article class="quick-stat">
          <span>包裹数量</span>
          <strong>{{ packageSummary.count }}</strong>
          <small>总重量 {{ packageSummary.total }}</small>
        </article>
      </div>

      <label class="field">
        <span>每架无人机最大载重</span>
        <textarea v-model="form.capacities" rows="4" />
      </label>

      <label class="field">
        <span>每个包裹重量</span>
        <textarea v-model="form.packages" rows="5" />
      </label>

      <div class="actions">
        <button class="primary" :disabled="loading" @click="optimize">
          {{ loading ? "计算中..." : "开始优化" }}
        </button>
        <button class="secondary" :disabled="loading" @click="fillExample">示例数据</button>
        <button class="ghost" :disabled="loading" @click="resetForm">重置</button>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </aside>

    <main class="content-area">
      <section class="hero-card">
        <div class="hero-grid">
          <div>
            <p class="eyebrow">乡村低空物流场景</p>
            <h1>农村无人机智能物流配送方案</h1>
            <p class="hero-kicker">智能装载优化与配送分析</p>
            <p class="hero-copy">
              围绕农村地区末端配送、多点协同与载重约束，展示无人机配送任务的输入、优化结果和全过程分析。
            </p>
            <div class="badge-row">
              <span v-for="badge in badges" :key="badge" class="badge">{{ badge }}</span>
            </div>
          </div>

          <div class="hero-sidecard">
            <p class="hero-sidecard-title">系统概览</p>
            <div class="hero-highlights">
              <article v-for="item in systemHighlights" :key="item.label" class="hero-highlight">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="transition-band" aria-hidden="true">
        <div class="transition-orb transition-orb-warm"></div>
        <div class="transition-line"></div>
        <div class="transition-orb transition-orb-cool"></div>
      </section>

      <template v-if="result">
        <section class="stats-grid">
          <article v-for="item in dashboardStats" :key="item.key" class="stat-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.note }}</small>
          </article>
        </section>

        <section class="summary-band">
          <article class="summary-panel summary-panel-primary">
            <span>配送结论</span>
            <strong>{{ result.undelivered === 0 ? "全部包裹可配送" : `仍有 ${result.undelivered} 重量待分配` }}</strong>
            <p>当前最优装载为 {{ result.best_load.join(" / ") }}，系统已给出可执行分配结果。</p>
          </article>
          <article class="summary-panel">
            <span>任务概览</span>
            <strong>{{ result.packages.length }} 件包裹 / {{ result.capacities.length }} 架无人机</strong>
            <p>总包裹重量 {{ result.package_total }}，总载重能力 {{ result.total_capacity }}。</p>
          </article>
        </section>

        <section class="panel table-panel">
          <div class="section-head">
            <h3>最优装载明细</h3>
            <p>每架无人机的最大载重、实际装载和剩余容量。</p>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>无人机</th>
                  <th>最大载重</th>
                  <th>实际装载</th>
                  <th>剩余容量</th>
                  <th>利用率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in result.result_rows" :key="row.drone">
                  <td>{{ row.drone }}</td>
                  <td>{{ row.capacity }}</td>
                  <td>{{ row.actual_load }}</td>
                  <td>{{ row.remaining }}</td>
                  <td>{{ row.utilization }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="charts-grid">
          <article class="panel">
            <div class="section-head">
              <h3>包裹重量排序图</h3>
              <p>按重量降序展示包裹分布。</p>
            </div>
            <div class="bar-list">
              <div v-for="item in packageBars" :key="item.label" class="bar-item">
                <span>{{ item.label }}</span>
                <div class="bar-track">
                  <div class="bar-fill warm" :style="{ width: `${item.ratio}%` }"></div>
                </div>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="section-head">
              <h3>无人机载重对比</h3>
              <p>同时展示最大载重和实际装载。</p>
            </div>
            <div class="dual-list">
              <div v-for="item in loadBars" :key="item.label" class="dual-item">
                <div class="dual-head">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.load }} / {{ item.capacity }}</strong>
                </div>
                <div class="bar-track soft">
                  <div class="bar-fill olive" :style="{ width: `${item.capacityRatio}%` }"></div>
                </div>
                <div class="bar-track">
                  <div class="bar-fill blue" :style="{ width: `${item.loadRatio}%` }"></div>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section class="panel table-panel">
          <div class="section-head">
            <h3>装载过程表</h3>
            <p>保留搜索得到的每一步有效装载结果。</p>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>步骤</th>
                  <th v-for="(_, idx) in result.best_load" :key="idx">无人机{{ idx + 1 }}</th>
                  <th>当前总装载</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in processRows" :key="row.step">
                  <td>{{ row.step }}</td>
                  <td v-for="(load, idx) in row.loads" :key="`${row.step}-${idx}`">{{ load }}</td>
                  <td>{{ row.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <section v-else class="empty-state panel">
        <h3>等待计算</h3>
        <p>左侧输入无人机和包裹数据后，点击“开始优化”即可生成完整的最优装载分析、图表和过程追踪。</p>
      </section>
    </main>
  </div>
</template>
