<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="submitSuccess" class="banner success-banner">{{ submitSuccess }}</div>
      <div v-if="submitError" class="banner error-banner">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-row">
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          <input
            type="range"
            min="0"
            max="25000"
            step="250"
            v-model.number="budget"
            class="budget-slider"
          >
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.availableBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.recommendedItems') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.totalRecommendedCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalRecommendedCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
        </div>
        <div v-if="recommendations.length === 0" class="loading">
          {{ t('restocking.emptyRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.shortfall }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ item.recommended_qty }}</strong></td>
                <td><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</strong></td>
                <td>{{ item.lead_time_days }}</td>
                <td>{{ item.supplier_name }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(5000)
    const submitting = ref(false)
    const submitSuccess = ref(null)
    const submitError = ref(null)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // 1. Items with a positive shortfall (forecasted demand exceeds current stock)
    const candidateItems = computed(() => {
      return forecasts.value
        .map(item => ({
          ...item,
          shortfall: item.forecasted_demand - item.current_stock
        }))
        .filter(item => item.shortfall > 0)
    })

    // 2. Increasing-trend items first (by shortfall desc), then the rest (by shortfall desc)
    const prioritizedItems = computed(() => {
      const increasing = candidateItems.value
        .filter(item => item.trend === 'increasing')
        .sort((a, b) => b.shortfall - a.shortfall)

      const others = candidateItems.value
        .filter(item => item.trend !== 'increasing')
        .sort((a, b) => b.shortfall - a.shortfall)

      return [...increasing, ...others]
    })

    // 3. Walk prioritized items, allocating budget until it runs out
    const recommendations = computed(() => {
      const result = []
      let remaining = budget.value

      for (const item of prioritizedItems.value) {
        if (remaining <= 0) break

        const qty = Math.min(item.shortfall, Math.floor(remaining / item.unit_cost))
        if (qty > 0) {
          const line_total = qty * item.unit_cost
          result.push({ ...item, recommended_qty: qty, line_total })
          remaining -= line_total
        }
      }

      return result
    })

    // 4. Cost/budget rollups
    const totalRecommendedCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.line_total, 0)
    })

    const remainingBudget = computed(() => budget.value - totalRecommendedCost.value)

    const placeOrder = async () => {
      submitting.value = true
      submitSuccess.value = null
      submitError.value = null

      try {
        const payloads = recommendations.value.map(item => ({
          item_sku: item.item_sku,
          item_name: item.item_name,
          supplier_name: item.supplier_name,
          quantity: item.recommended_qty,
          unit_cost: item.unit_cost,
          lead_time_days: item.lead_time_days,
          notes: 'Restocking order generated from demand forecast'
        }))

        await Promise.all(payloads.map(payload => api.createPurchaseOrder(payload)))

        submitSuccess.value = t('restocking.submitSuccess', { count: payloads.length })
      } catch (err) {
        submitError.value = t('restocking.submitError') + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      currencySymbol,
      candidateItems,
      prioritizedItems,
      recommendations,
      totalRecommendedCost,
      remainingBudget,
      submitting,
      submitSuccess,
      submitError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 110px;
  letter-spacing: -0.025em;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 8px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider:focus {
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: background 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: background 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 8px;
  background: #e2e8f0;
}

.place-order-btn {
  margin-top: 1rem;
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.banner {
  padding: 0.875rem 1.125rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.success-banner {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.error-banner {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
</style>
