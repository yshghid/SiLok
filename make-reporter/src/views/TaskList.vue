<template>
  <div class="task-wrapper">
    <!-- 제목 -->
    <div class="page-title-box">
      <h1 class="page-title">주간보고서 만들기</h1>
    </div>
    <!-- 확인용 주석 -->
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
            <button class="auth-btn" @click="logout" style="background-color: #dc3545;">로그아웃</button>
          </div>
        </div>

        <!-- 안내문 -->
        <div class="task-info">
          <div v-if="!userInfo" class="error-message">로그인이 필요합니다.</div>
          <span v-else-if="startDate && endDate">
            {{ userName }}님의
            {{ formatDate(startDate) }} ~ {{ formatDate(endDate) }} 의 업무 내용입니다.
          </span>
          <div v-if="loading" class="loading-message">데이터를 불러오는 중...</div>
          <div v-if="error" class="error-message">{{ error }}</div>
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
              <tr v-if="filteredTasks.length === 0 && !loading">
                <td colspan="6" class="no-data">선택한 기간에 데이터가 없습니다.</td>
              </tr>
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
import { ref, computed, onMounted } from "vue";
import "../styles/tasklist.css";

// 로그인한 사용자 정보
const userInfo = ref(null);
const userName = ref("");
const userEmail = ref("");

// localStorage에서 사용자 정보 가져오기
const loadUserInfo = () => {
  const storedUserInfo = localStorage.getItem('userInfo');
  if (storedUserInfo) {
    userInfo.value = JSON.parse(storedUserInfo);
    userName.value = userInfo.value.name;
    userEmail.value = userInfo.value.email;
    console.log('TaskList에서 로드된 사용자 정보:', userInfo.value);
  } else {
    // 로그인 정보가 없으면 로그인 페이지로 리다이렉트
    console.log('로그인 정보가 없습니다. 로그인 페이지로 이동합니다.');
    // router.push('/');
  }
};

// 컴포넌트 마운트 시 사용자 정보 로드
onMounted(() => {
  loadUserInfo();
});

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

// 실제 업무 데이터 (API에서 가져옴)
const tasks = ref([]);
const filteredTasks = ref([]);
const selectAll = ref(false);
const loading = ref(false);
const error = ref(null);

// API 호출 함수
const fetchUserTimeline = async () => {
  if (!userInfo.value) {
    error.value = "로그인이 필요합니다.";
    return;
  }
  
  if (!startDate.value || !endDate.value) {
    error.value = "시작일과 종료일을 선택해주세요.";
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // POST 요청을 위한 시간 포함 날짜 포맷팅
    const startDateStr = formatDateTimeForAPI(startDate.value);
    const endDateStr = formatDateTimeForAPI(endDate.value);
    
    const response = await fetch(
      `http://127.0.0.1:8001/api/user-timeline`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userName.value,
          start_date: startDateStr,
          end_date: endDateStr
        })
      }
    );
    
    if (!response.ok) {
      throw new Error(`API 호출 실패: ${response.status}`);
    }
    
    const data = await response.json();
    
    // API 응답을 테이블 형식으로 변환
    tasks.value = data.activities.map(activity => ({
      datetime: formatDateTime(activity.timestamp),
      platform: getPlatformName(activity.source),
      sender: activity.metadata.sender || activity.metadata.writer || "시스템",
      receiver: activity.metadata.receiver || activity.metadata.participants || "시스템",
      content: activity.content,
      checked: false
    }));
    
    filteredTasks.value = [...tasks.value];
    
  } catch (err) {
    error.value = `데이터를 가져오는 중 오류가 발생했습니다: ${err.message}`;
    console.error("API 호출 오류:", err);
  } finally {
    loading.value = false;
  }
};

// API용 날짜 포맷팅 (GET 요청용 - 날짜만)
const formatDateForAPI = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// API용 날짜시간 포맷팅 (POST 요청용 - 시간 포함)
const formatDateTimeForAPI = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
};

// 표시용 날짜시간 포맷팅
const formatDateTime = (timestamp) => {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 플랫폼 이름 변환
const getPlatformName = (source) => {
  const platformMap = {
    'slack': 'Slack',
    'notion': 'Notion',
    'onedrive': 'OneDrive',
    'outlook': 'Outlook'
  };
  return platformMap[source] || source;
};

const filterTasks = () => {
  if (startDate.value && endDate.value) {
    fetchUserTimeline();
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

// 보고서 생성 함수
const generateReport = () => {
  const selectedTasks = filteredTasks.value.filter(task => task.checked);
  if (selectedTasks.length === 0) {
    alert("보고서에 포함할 업무를 선택해주세요.");
    return;
  }
  
  // 여기에 보고서 생성 로직 추가
  console.log("선택된 업무:", selectedTasks);
  alert(`${selectedTasks.length}개의 업무가 선택되었습니다. 보고서 생성 기능은 추후 구현됩니다.`);
};

// 로그아웃 함수
const logout = () => {
  localStorage.removeItem('userInfo');
  userInfo.value = null;
  userName.value = "";
  userEmail.value = "";
  console.log('로그아웃되었습니다.');
  // router.push('/');
};
</script>
