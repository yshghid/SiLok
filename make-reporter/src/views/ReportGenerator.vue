<template>
  <div class="report-generator-wrapper">
    <div class="page-title-box">
      <h1 class="page-title">Reportify</h1>
    </div>

    <div class="content">
      <!-- 왼쪽: 캘린더 + 드롭다운 + 확인 버튼 -->
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

        <!-- Task ID 입력 -->
        <div class="input-section">
          <label for="task-id">Task ID:</label>
          <input
            id="task-id"
            v-model.number="taskId"
            type="number"
            class="input-field"
            placeholder="Task ID를 입력하세요"
          />
        </div>

        <!-- 확인 버튼 -->
        <div class="button-section">
          <button class="confirm-btn" @click="generateReport" :disabled="!canGenerate">
            보고서 생성
          </button>
        </div>
      </div>

      <!-- 오른쪽: 보고서 결과 텍스트 -->
      <div class="right-box">
        <h2>보고서 내용</h2>
        <div class="report-content">
          <div v-if="loading" class="loading-message">
            보고서를 생성하는 중입니다...
          </div>
          <div v-else-if="error" class="error-message">
            {{ error }}
          </div>
          <div v-else-if="reportText" class="report-text" v-html="renderedMarkdown">
          </div>
          <div v-if="reportText" class="download-section">
            <button class="download-btn" @click="downloadAsWord">
              📄 Word 파일로 다운로드
            </button>
          </div>
          <div v-else class="placeholder-text">
            캘린더에서 날짜를 선택하고 Task ID를 입력한 후 '보고서 생성' 버튼을 클릭하세요.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { marked } from 'marked';
import { saveAs } from 'file-saver';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import "../styles/report-generator.css";

// 로그인한 사용자 정보
const userInfo = ref(null);
const userName = ref("");

// localStorage에서 사용자 정보 가져오기
const loadUserInfo = () => {
  const storedUserInfo = localStorage.getItem('userInfo');
  if (storedUserInfo) {
    userInfo.value = JSON.parse(storedUserInfo);
    userName.value = userInfo.value.name;
  }
};

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

// Task ID 입력값
const taskId = ref(null);

// 보고서 상태
const reportText = ref("");
const loading = ref(false);
const error = ref(null);

// 마크다운을 HTML로 렌더링 (날짜 및 Task ID 정보 포함)
const renderedMarkdown = computed(() => {
  if (!reportText.value) return "";

  // 보고서 내용 앞에 날짜 및 Task ID 정보 추가
  const dateInfo = formatDateForDisplay(startDate.value);
  const endDateInfo = formatDateForDisplay(endDate.value);
  const headerInfo = `**주간 업무 요약**\n\n- **Task ID**: ${taskId.value}\n- **보고 기간**: ${dateInfo} ~ ${endDateInfo}\n\n---\n\n`;

  const fullContent = headerInfo + reportText.value;
  return marked(fullContent);
});

// 날짜를 표시용으로 포맷팅
const formatDateForDisplay = (date) => {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}년 ${month}월 ${day}일`;
};

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

// 보고서 생성 가능 여부
const canGenerate = computed(() => {
  return startDate.value && endDate.value && taskId.value;
});

// API용 날짜 포맷팅 (날짜만)
const formatDateForAPI = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// 보고서 생성 함수
const generateReport = async () => {
  if (!canGenerate.value) {
    error.value = "날짜와 Task ID를 모두 입력해주세요.";
    return;
  }

  loading.value = true;
  error.value = null;
  reportText.value = "";

  try {
    const startDateStr = formatDateForAPI(startDate.value);
    const endDateStr = formatDateForAPI(endDate.value);

    const response = await fetch('http://127.0.0.1:8001/api/generate-summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId.value,
        start_date: startDateStr,
        end_date: endDateStr
      })
    });

    if (!response.ok) {
      throw new Error(`API 호출 실패: ${response.status}`);
    }

    const data = await response.json();
    reportText.value = data.summary || "보고서가 생성되었습니다.";

  } catch (err) {
    error.value = `보고서 생성 중 오류가 발생했습니다: ${err.message}`;
    console.error("보고서 생성 오류:", err);
  } finally {
    loading.value = false;
  }
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

// Word 파일 다운로드 기능
const downloadAsWord = async () => {
  if (!reportText.value) return;

  try {
    // 날짜 정보
    const dateInfo = formatDateForDisplay(startDate.value);
    const endDateInfo = formatDateForDisplay(endDate.value);

    // 마크다운 제거된 텍스트
    const cleanText = removeMarkdown(reportText.value);

    // Word 문서 생성
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          // 제목
          new Paragraph({
            children: [new TextRun({ text: "주간 업무 요약 보고서", bold: true, size: 32 })],
            heading: HeadingLevel.HEADING_1,
          }),

          // 빈 줄
          new Paragraph({ children: [new TextRun("")] }),

          // Task ID
          new Paragraph({
            children: [
              new TextRun({ text: "Task ID: ", bold: true }),
              new TextRun({ text: taskId.value.toString() })
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

    // 파일명 생성 (더 현실적인 형태)
    // 주차 계산 (시작 날짜 기준)
    const startDateObj = startDate.value;
    const weekNumber = Math.ceil(startDateObj.getDate() / 7);
    const monthStr = String(startDateObj.getMonth() + 1).padStart(2, '0');

    const filename = `Task${taskId.value}_${startDateObj.getFullYear()}년${monthStr}월${weekNumber}주차_주간업무요약보고서.docx`;

    // 다운로드
    saveAs(blob, filename);

  } catch (error) {
    console.error('다운로드 오류:', error);
    alert('파일 다운로드 중 오류가 발생했습니다.');
  }
};
</script>