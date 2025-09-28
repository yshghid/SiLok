<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import "../styles/login.css";

const router = useRouter();

const isSignUp = ref(false);

const loginEmail = ref("");
const loginPw = ref("");

const signUpName = ref("");
const signUpEmail = ref("");
const signUpPw = ref("");

// 로그인
const onLogin = async () => {
  try {
    const res = await axios.post("http://127.0.0.1:8001/login", {
      email: loginEmail.value,
      password: loginPw.value,
    });
    if (res.data.success) {
      // 로그인한 사용자 정보를 localStorage에 저장
      const userInfo = {
        id: res.data.user.id,
        name: res.data.user.name,
        email: res.data.user.email,
        password: loginPw.value // 실제로는 저장하지 않는 것이 좋지만 테스트용
      };
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
      console.log('로그인된 사용자 정보:', userInfo);
      
      if (res.data.user.id == "5") {
        router.push("/report-generator")
      } else {
        router.push("/tasks");
      }
    }
  } catch (err) {
    alert(err.response?.data?.detail || "로그인 실패");
  }
};

// 회원가입
const onSignUp = async () => {
  try {
    await axios.post("http://127.0.0.1:8001/signup", {
      name: signUpName.value,
      email: signUpEmail.value,
      password: signUpPw.value,
    });
    alert("회원가입 성공! 로그인 해주세요.");
    isSignUp.value = false;
  } catch (err) {
    alert(err.response?.data?.detail || "회원가입 실패");
  }
};
</script>

<template>
  <div class="auth-wrapper">
    <!-- 로그인 화면 -->
    <div v-if="!isSignUp" class="auth-box">
      <h1 class="project-title">SILOK</h1>
      <label>이메일</label>
      <input type="email" v-model="loginEmail" />
      <label>비밀번호</label>
      <input type="password" v-model="loginPw" />
      <button class="auth-btn" @click="onLogin">로그인</button>
      <button class="auth-btn" @click="isSignUp = true">회원가입</button>
    </div>

    <!-- 회원가입 화면 -->
    <div v-else class="auth-box">
      <h1 class="project-title">SILOK</h1>
      <label>이름</label>
      <input type="text" v-model="signUpName" />
      <label>이메일</label>
      <input type="email" v-model="signUpEmail" />
      <label>비밀번호</label>
      <input type="password" v-model="signUpPw" />
      <button class="auth-btn" @click="onSignUp">회원가입하기</button>
      <button class="auth-btn" @click="isSignUp = false">뒤로가기</button>
    </div>
  </div>
</template>
