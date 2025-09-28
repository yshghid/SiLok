import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import TaskList from "../views/TaskList.vue";
import ReportGenerator from "../views/ReportGenerator.vue";

const routes = [
  { path: "/", name: "Login", component: Login },
  { path: "/tasks", name: "TaskList", component: TaskList },
  { path: "/report-generator", name: "ReportGenerator", component: ReportGenerator },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
