<template>
  <div class="task-wrapper">
    <!-- 제목 -->
    <div class="page-title-box">
      <h1 class="page-title">주간보고서 만들기</h1>
    </div>

    <div class="content">
      <!-- 왼쪽: 캘린더 + 버튼 + 테이블 -->
      <div class="left-box">
        <!-- 캘린더 -->
        <div class="calendar-section">
          <div class="calendar-header">
            <button @click="prevMonth">&lt;</button>
            <span>{{ currentYear }}년 {{ currentMonth + 1 }}월</span>
            <button @click="nextMonth">&gt;</button>
          </div>
          <div class="calendar-grid">
            <div class="day-name" v-for="d in dayNames" :key="d">{{ d }}</div>
            <div
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="day"
              :class="dayClass(day)"
              @click="selectDate(day)"
            >
              {{ !isNaN(day) ? day.getDate() : "" }}
            </div>
          </div>
        </div>

        <!-- 버튼 -->
        <div class="task-controls">
          <div class="btn-group">
            <button class="auth-btn" @click="filterTasks">업무 리스트업</button>
            <button class="auth-btn" @click="resetTasks">리스트 초기화</button>
            <button class="auth-btn" @click="generateReport">보고서 생성</button>
          </div>
        </div>

        <!-- 안내문 -->
        <div class="task-info">
          <span v-if="startDate && endDate">
            {{ userName }}님의
            {{ formatDate(startDate) }} ~ {{ formatDate(endDate) }} 의 업무 내용입니다.
          </span>
        </div>

        <!-- 업무 테이블 -->
        <div class="table-container">
          <table class="task-table">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" v-model="selectAll" @change="toggleAll" />
                </th>
                <th>날짜/시간</th>
                <th>플랫폼</th>
                <th>송신자</th>
                <th>수신자</th>
                <th>내용</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(task, idx) in displayedTasks" :key="idx">
                <td>
                  <input type="checkbox" v-model="task.checked" v-if="task.datetime" />
                </td>
                <td>{{ task.datetime }}</td>
                <td>{{ task.platform }}</td>
                <td>{{ task.sender }}</td>
                <td>{{ task.receiver }}</td>
                <td>{{ task.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 오른쪽: 분석 보고서 -->
      <div class="right-box">
        <h2>분석 보고서</h2>
        <p>여기에 분석 결과가 출력됩니다.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import "../styles/tasklist.css";

const userName = "범준";

// 현재 월/연도
const today = new Date();
const currentYear = ref(today.getFullYear());
const currentMonth = ref(today.getMonth());

// 선택 날짜
const startDate = ref(null);
const endDate = ref(null);

// 요일 이름
const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// 달력 생성
const calendarDays = computed(() => {
  const firstDay = new Date(currentYear.value, currentMonth.value, 1);
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0);
  const days = [];

  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push(new Date(NaN));
  }
  for (let d = 1; d <= lastDay.getDate(); d++) {
    days.push(new Date(currentYear.value, currentMonth.value, d));
  }
  return days;
});

// 날짜 선택
const selectDate = (day) => {
  if (isNaN(day)) return;
  if (!startDate.value || (startDate.value && endDate.value)) {
    startDate.value = day;
    endDate.value = null;
  } else if (!endDate.value) {
    if (day >= startDate.value) {
      endDate.value = day;
    } else {
      endDate.value = startDate.value;
      startDate.value = day;
    }
  }
};

// 날짜 스타일
const dayClass = (day) => {
  if (isNaN(day)) return "empty";
  if (startDate.value && day.getTime() === startDate.value.getTime()) {
    return "start-day";
  }
  if (endDate.value && day.getTime() === endDate.value.getTime()) {
    return "end-day";
  }
  if (
    startDate.value &&
    endDate.value &&
    day > startDate.value &&
    day < endDate.value
  ) {
    return "in-range";
  }
  return "";
};

// 달 이동
const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11;
    currentYear.value--;
  } else {
    currentMonth.value--;
  }
};
const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0;
    currentYear.value++;
  } else {
    currentMonth.value++;
  }
};

// 더미 업무 데이터
const tasks = ref([
  { datetime: "2025-09-15 09:00", platform: "이메일", sender: "김대리", receiver: "범준", content: "주간 보고서 송부", checked: false },
  { datetime: "2025-09-16 14:00", platform: "메신저", sender: "박과장", receiver: "범준", content: "회의 일정 조율", checked: false },
  { datetime: "2025-09-18 16:30", platform: "시스템", sender: "자동알림", receiver: "범준", content: "서버 점검 완료", checked: false },
    { datetime: "2025-09-15 09:00", platform: "이메일", sender: "김대리", receiver: "범준", content: "주간 보고서 송부", checked: false },
  { datetime: "2025-09-16 14:00", platform: "메신저", sender: "박과장", receiver: "범준", content: "회의 일정 조율", checked: false },
  { datetime: "2025-09-18 16:30", platform: "시스템", sender: "자동알림", receiver: "범준", content: "서버 점검 완료", checked: false },
    { datetime: "2025-09-15 09:00", platform: "이메일", sender: "김대리", receiver: "범준", content: "주간 보고서 송부", checked: false },
  { datetime: "2025-09-16 14:00", platform: "메신저", sender: "박과장", receiver: "범준", content: "회의 일정 조율", checked: false },
  { datetime: "2025-09-18 16:30", platform: "시스템", sender: "자동알림", receiver: "범준", content: "서버 점검 완료", checked: false },
    { datetime: "2025-09-15 09:00", platform: "이메일", sender: "김대리", receiver: "범준", content: "주간 보고서 송부", checked: false },
  { datetime: "2025-09-16 14:00", platform: "메신저", sender: "박과장", receiver: "범준", content: "회의 일정 조율", checked: false },
  { datetime: "2025-09-18 16:30", platform: "시스템", sender: "자동알림", receiver: "범준", content: "서버 점검 완료", checked: false },
]);

const filteredTasks = ref([]);
const selectAll = ref(false);

const filterTasks = () => {
  if (startDate.value && endDate.value) {
    filteredTasks.value = tasks.value.filter((t) => {
      const taskDate = new Date(t.datetime);
      return taskDate >= startDate.value && taskDate <= endDate.value;
    });
  }
};

const resetTasks = () => {
  startDate.value = null;
  endDate.value = null;
  filteredTasks.value = [];
  selectAll.value = false;
  tasks.value.forEach((t) => (t.checked = false));
};

// 8줄 고정
const displayedTasks = computed(() => {
  const rows = [...filteredTasks.value];
  while (rows.length < 8) {
    rows.push({ datetime: "", platform: "", sender: "", receiver: "", content: "" });
  }
  return rows;
});

const toggleAll = () => {
  filteredTasks.value.forEach((t) => (t.checked = selectAll.value));
};

const formatDate = (date) => {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};
</script>
