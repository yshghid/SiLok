import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import TaskList from "../views/TaskList.vue";

const routes = [
  { path: "/", name: "Login", component: Login },
  { path: "/tasks", name: "TaskList", component: TaskList },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
