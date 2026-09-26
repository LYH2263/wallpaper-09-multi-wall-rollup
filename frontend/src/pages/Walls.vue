<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getJSON } from '../api'
const items = ref([])
// 勾选状态即请求体来源：带到测算台后直接成为 wall_ids
const picked = ref([])
const router = useRouter()
onMounted(async () => { items.value = (await getJSON('/api/walls')).items })
function goBench() {
  if (!picked.value.length) return
  router.push({ path: '/bench', query: { walls: picked.value.join(',') } })
}
</script>
<template>
  <div class="page"><h1>墙面列表</h1>
  <table>
    <tr v-for="w in items" :key="w.id">
      <td><input type="checkbox" v-model="picked" :value="w.id" :disabled="w.data_quality==='dirty'" /></td>
      <td>{{ w.name }}</td>
      <td>{{ w.perimeter }}m</td>
      <td v-if="w.data_quality==='dirty'" class="warn">脏数据不可试算</td>
      <td><router-link :to="`/walls/${w.id}`">详情</router-link></td>
    </tr>
  </table>
  <button :disabled="!picked.length" @click="goBench">在测算台合并试算（{{ picked.length }}）</button>
  </div>
</template>
