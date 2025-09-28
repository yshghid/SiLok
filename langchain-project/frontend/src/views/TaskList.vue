<template>
  <div class="task-wrapper">
    <!-- 제목 -->
    <div class="page-title-box">
      <h1 class="page-title">SILOK</h1>
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
            <div v-for="(day, idx) in calendarDays" :key="idx" class="day" :class="dayClass(day)"
              @click="selectDate(day)">
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

      <!-- 오른쪽: 주간업무 보고서 -->
      <div class="right-box">
        <h2>업무 보고서 내용</h2>

        <!-- 보고서 생성 중일 때 로딩 스피너 -->
        <div v-if="reportLoading" class="spinner-wrapper">
          <div class="spinner"></div>
          <p>보고서를 생성 중입니다...</p>
        </div>

        <!-- 보고서가 있을 때 -->
        <div v-else-if="analysisReports.length > 0" class="analysis-content">
          <div v-for="(report, idx) in analysisReports" :key="idx" class="single-report">
            <div v-html="formatAnalysisReport(report)"></div>
            <hr />
          </div>

          <!-- Word 파일 다운로드 버튼 -->
          <div class="download-section">
            <button class="download-btn" @click="downloadAsWord">
              📄 Word 파일로 다운로드
            </button>
          </div>
        </div>

        <!-- 보고서가 없을 때 -->
        <div v-else class="no-analysis">
          <p>보고서를 생성하면 분석 결과가 여기에 표시됩니다.</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { saveAs } from 'file-saver';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import "../styles/tasklist.css";

// 로그인한 사용자 정보
const userInfo = ref(null);
const userName = ref("");
const userEmail = ref("");

const router = useRouter();

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
const analysisReports = ref([]);
const reportLoading = ref(false);  // 보고서 생성 로딩 상태

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
      `http://127.0.0.1:8001/api/user-timeline/${userEmail.value}?start_date=${formatDateForAPI(startDate.value)}&end_date=${formatDateForAPI(endDate.value)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      throw new Error(`API 호출 실패: ${response.status}`);
    }

    const data = await response.json();

    // API 응답을 테이블 형식으로 변환
    tasks.value = data.activities.map((activity, index) => {
      // 각 플랫폼별로 실제 ID 추출
      let actualId = null;
      if (activity.source === 'slack' && activity.metadata.slack_id) {
        actualId = activity.metadata.slack_id;
      } else if (activity.metadata.id) {
        actualId = activity.metadata.id;
      } else {
        actualId = index + 1; // fallback
      }

      return {
        id: actualId,
        platform: getPlatformName(activity.source),
        datetime: formatDateTime(activity.timestamp),
        sender: activity.metadata.sender || activity.metadata.writer || "시스템",
        receiver: activity.metadata.receiver || activity.metadata.participants || "시스템",
        content: activity.content,
        checked: false,
        source: activity.source // 원본 소스 정보 보존
      };
    });

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
const generateReport = async () => {
  const selectedTasks = filteredTasks.value.filter(task => task.checked);
  if (selectedTasks.length === 0) {
    alert("보고서에 포함할 업무를 선택해주세요.");
    return;
  }

  if (!startDate.value || !endDate.value) {
    alert("시작일과 종료일을 선택해주세요.");
    return;
  }
  reportLoading.value = true;  // 보고서 생성 시작

  try {
    // 선택된 업무들을 플랫폼별로 ID 수집
    const platformIds = {
      slack: [],
      notion: [],
      outlook: [],
      onedrive: []
    };

    // 선택된 업무들을 플랫폼별로 ID 수집
    selectedTasks.forEach((task) => {
      const id = task.id;
      // source 정보를 기반으로 플랫폼 분류
      switch (task.source) {
        case 'slack':
          platformIds.slack.push(id);
          break;
        case 'notion':
          platformIds.notion.push(id);
          break;
        case 'outlook':
          platformIds.outlook.push(id);
          break;
        case 'onedrive':
          platformIds.onedrive.push(id);
          break;
        default:
          // platform 이름으로 fallback
          switch (task.platform) {
            case 'Slack':
              platformIds.slack.push(id);
              break;
            case 'Notion':
              platformIds.notion.push(id);
              break;
            case 'Outlook':
              platformIds.outlook.push(id);
              break;
            case 'OneDrive':
              platformIds.onedrive.push(id);
              break;
            default:
              platformIds.slack.push(id);
              break;
          }
          break;
      }
    });

    console.log('선택된 플랫폼 ID:', platformIds);

    const requestData = {
      platform_ids: platformIds,
      start: formatDateForAPI(startDate.value),
      end: formatDateForAPI(endDate.value),
      email: userEmail.value,
      writer: userName.value
    };


    console.log('보고서 생성 요청 데이터:', requestData);

    const response = await fetch('http://127.0.0.1:8001/reports/weekly', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });

    console.log('API 응답 상태:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API 오류 응답:', errorText);
      throw new Error(`보고서 생성 실패: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log('보고서 생성 결과:', result);

    // 분석보고서를 오른쪽 박스에 표시
    displayAnalysisReport(result);

  } catch (error) {
    console.error('보고서 생성 오류:', error);
    alert(`보고서 생성 중 오류가 발생했습니다: ${error.message}`);
  }
  finally{
    reportLoading.value = false;  // 보고서 생성 종료
  }
};

// 분석보고서 표시 함수
const displayAnalysisReport = (result) => {
  if (result.reports && Array.isArray(result.reports)) {
    analysisReports.value = result.reports.map(r => r.report);
  } else {
    analysisReports.value = [];
  }
};

const formatAnalysisReport = (report) => {
  if (!report) return '';

  let html = report;

  // 헤더 변환 (# ## ### #### → 테마 색상 적용)
  html = html.replace(/^#### (.*$)/gm, '<h6 class="md-title">$1</h6>');
  html = html.replace(/^### (.*$)/gm, '<h5 class="md-title">$1</h5>');
  html = html.replace(/^## (.*$)/gm, '<h4 class="md-title">$1</h4>');
  html = html.replace(/^# (.*$)/gm, '<h3 class="md-title">$1</h3>');

  // 강조 텍스트 변환
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // 코드 블록 변환 (```로 감싸진 부분)
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

  // 인라인 코드 변환 (`로 감싸진 부분)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // 링크 변환 [텍스트](URL)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  // 리스트 변환 (- 또는 *로 시작하는 줄)
  html = html.replace(/^[\s]*[-*] (.+)$/gm, '<li>$1</li>');

  // 연속된 <li> 태그를 <ul>로 감싸기
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

  // 줄바꿈 처리
  html = html.replace(/\n\n/g, '<br><br>');
  html = html.replace(/\n/g, '<br>');

  // 수평선 변환 (--- 또는 ***)
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^\*\*\*$/gm, '<hr>');

  return html;
};


// 마크다운 문법 제거 함수
const removeMarkdown = (text) => {
  return text
    // 제목 (#, ##, ###)
    .replace(/^#{1,6}\s+/gm, '')
    // 굵은 글씨 (**text**, __text__)
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    // 기울임 (*text*, _text_)
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    // 코드 블록 (```code```)
    .replace(/```[\s\S]*?```/g, '')
    // 인라인 코드 (`code`)
    .replace(/`([^`]+)`/g, '$1')
    // 링크 [text](url)
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // 이미지 ![alt](url)
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    // 목록 (-, *, +)
    .replace(/^[\s]*[-\*\+]\s+/gm, '• ')
    // 숫자 목록
    .replace(/^[\s]*\d+\.\s+/gm, '')
    // 인용문 (>)
    .replace(/^>\s+/gm, '')
    // 수평선 (---, ***)
    .replace(/^[-\*]{3,}$/gm, '─────────────────────────')
    // 여러 개의 연속된 공백을 하나로
    .replace(/\n{3,}/g, '\n\n')
    .trim();
};

// 날짜를 표시용으로 포맷팅
const formatDateForDisplay = (date) => {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}년 ${month}월 ${day}일`;
};

// Word 파일 다운로드 기능
const downloadAsWord = async () => {
  if (analysisReports.value.length === 0) return;

  try {
    // 날짜 정보
    const dateInfo = formatDateForDisplay(startDate.value);
    const endDateInfo = formatDateForDisplay(endDate.value);

    // 모든 보고서를 하나의 텍스트로 합치기
    const allReports = analysisReports.value.join('\n\n=================\n\n');

    // 마크다운 제거된 텍스트
    const cleanText = removeMarkdown(allReports);

    // Word 문서 생성
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          // 제목
          new Paragraph({
            children: [new TextRun({ text: "주간 업무 보고서", bold: true, size: 32 })],
            heading: HeadingLevel.HEADING_1,
          }),

          // 빈 줄
          new Paragraph({ children: [new TextRun("")] }),

          // 작성자 정보
          new Paragraph({
            children: [
              new TextRun({ text: "작성자: ", bold: true }),
              new TextRun({ text: userName.value })
            ]
          }),

          // 기간
          new Paragraph({
            children: [
              new TextRun({ text: "보고 기간: ", bold: true }),
              new TextRun({ text: `${dateInfo} ~ ${endDateInfo}` })
            ]
          }),

          // 구분선
          new Paragraph({ children: [new TextRun("─────────────────────────")] }),
          new Paragraph({ children: [new TextRun("")] }),

          // 보고서 내용 (마크다운 제거된 텍스트)
          ...cleanText.split('\n').map(line => {
            // 빈 줄 처리
            if (line.trim() === '') {
              return new Paragraph({ children: [new TextRun("")] });
            }

            // 제목처럼 보이는 줄 (대문자로 시작하고 끝에 :가 있는 경우) 굵게 처리
            if (line.match(/^[A-Z가-힣][^:]*:?\s*$/) || line.includes('##') || line.includes('**')) {
              return new Paragraph({
                children: [new TextRun({ text: line, bold: true })]
              });
            }

            // 구분선 처리
            if (line.includes('=================')) {
              return new Paragraph({
                children: [new TextRun({ text: "─────────────────────────", bold: true })]
              });
            }

            // 일반 텍스트
            return new Paragraph({
              children: [new TextRun({ text: line })]
            });
          })
        ],
      }],
    });

    // Word 문서를 blob으로 생성
    const blob = await Packer.toBlob(doc);

    // 파일명 생성
    const startDateObj = startDate.value;
    const weekNumber = Math.ceil(startDateObj.getDate() / 7);
    const monthStr = String(startDateObj.getMonth() + 1).padStart(2, '0');

    const filename = `${userName.value}_${startDateObj.getFullYear()}년${monthStr}월${weekNumber}주차_주간업무보고서.docx`;

    // 다운로드
    saveAs(blob, filename);

  } catch (error) {
    console.error('다운로드 오류:', error);
    alert('파일 다운로드 중 오류가 발생했습니다.');
  }
};

// 로그아웃 함수
const logout = () => {
  localStorage.removeItem('userInfo');
  userInfo.value = null;
  userName.value = "";
  userEmail.value = "";
  analysisReports.value = [];
  console.log('로그아웃되었습니다.');
  router.push('/');
};
</script>
