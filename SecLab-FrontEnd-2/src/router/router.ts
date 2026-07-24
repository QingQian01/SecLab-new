import { createRouter, createWebHashHistory } from "vue-router";
import UserLayout from "../layout/User/index.vue";
import AdminLayout from "../layout/Admin/index.vue";
import Courses from "../pages/User/Courses/index.vue";
import Welcome from "../pages/WelCome/index.vue";
import Course from "../pages/User/Course/index.vue";
import Module from "../pages/User/Module/index.vue";
import ScoreBoard from "../pages/User/Scoreboard/index.vue";
import Modules from "../pages/User/Modules/index.vue";
import Profile from "../pages/User/Profile/index.vue";
import Community from "../pages/User/Community/index.vue";
import Access from "../pages/Access/index.vue";
import UserManage from "../pages/Admin/Users/index.vue";
import CourseManage from "../pages/Admin/Courses/index.vue";
import LabManage from "../pages/Admin/Labs/index.vue";
import MockTarget from "../mock/MockTarget.vue";
import DashBoard from "../pages/Admin/DashBoard/index.vue";
import ClassProfile from "../pages/Admin/ClassProfile/index.vue";
import GeneratedQuestions from "../pages/Admin/GeneratedQuestions/index.vue";
import Chat from "../pages/User/Chat/index.vue";
import FloatingChatDemo from "../pages/User/Chat/FloatingChatDemo.vue";
import CourseCreate from "../pages/Admin/Courses/create/create.vue";
import AdminStudentProfile from "../pages/Admin/StudentProfile/index.vue";
import ModuleTest from "../pages/User/Module/test.vue";
import XssTest from "../pages/User/Module/xss-test.vue";
import CommandTest from "../pages/User/Module/command-test.vue";
import XSSDirect from "../pages/User/Module/xss-direct.vue";
import Training from "../pages/User/Training/index.vue";
// 队友教师端(Teacher)布局与页面
import TeacherLayout from "../layout/Teacher/index.vue";
import TeacherOverview from "../pages/Teacher/Overview/index.vue";
import TeachingClasses from "../pages/Teacher/TeachingClasses/index.vue";
import TeacherTeachingAnalysis from "../pages/Teacher/TeachingAnalysis/index.vue";
import TeacherCourseLibrary from "../pages/Teacher/CourseLibrary/index.vue";
import TeacherGeneratedQuestions from "../pages/Teacher/GeneratedQuestions/index.vue";
import { getUserInfo } from "../api";
import { clearStoredAuthSession, getStoredToken, isPrivilegedRole, normalizeCurrentUser, storeAuthSession } from "../auth";
import { isLabRunning } from "../composables/useLabState";

export const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/container/550e8400-e29b-41d4-a716-446655440000",
            component: MockTarget
        },
        {
            path: "/user",
            component: UserLayout,
            children: [
                {
                    path: "training/cmd-inject-bypass",
                    component: Training
                },
                {
                    path: "",
                    redirect: "/user/welcome"
                },
                {
                    path: "welcome",
                    component: Welcome
                },
                {
                    path: "courses",
                    component: Courses
                },
                {
                    path: "course/:id",
                    component: Course
                },
                {
                    path: "module/:id",
                    component: Module
                },
                {
                    path: "module",
                    component: Module
                },
                {
                    path: "community",
                    component: Community
                },
                {
                    path: "scoreboard",
                    component: ScoreBoard
                },
                {
                    path: "modules",
                    component: Modules
                },
                {
                    path: "profile",
                    component: Profile
                },
                {
                    path: "chat",
                    component: Chat
                },
                {
                    path: "floating-chat-demo",
                    component: FloatingChatDemo
                },
                {
                    path: "module-test",
                    component: ModuleTest
                },
                {
                    path: "xss-test",
                    component: XssTest
                },
                {
                    path: "command-test",
                    component: CommandTest
                },
                {
                    path: "xss-direct",
                    component: XSSDirect
                }
            ]
        },
        {
            path: "/admin",
            component: AdminLayout,
            children: [
                {
                    path: "",
                    redirect: "/admin/dashboard"
                },
                // 在admin路径下
                {
                    path: "course/create",
                    component: CourseCreate
                },
                {
                    path: "course/:id/edit",
                    component: CourseCreate
                },
                {
                    path: "welcome",
                    component: Welcome
                },
                {
                    path: "user",
                    component: UserManage
                },
                {
                    path: "course",
                    component: CourseManage
                },
                {
                    path: "lab",
                    component: LabManage
                },
                {
                    path: "class-profile",
                    component: ClassProfile
                },
                {
                    path: "generated-questions",
                    component: GeneratedQuestions
                },
                {
                    path: "student-profile/:id",
                    component: AdminStudentProfile
                },
                {
                    path: "dashboard",
                    component: DashBoard
                }
            ]
        },
        {
            // 队友新增：教师端（教学班/教学分析/课程库/生成题目），与 /admin 并存
            path: "/teacher",
            component: TeacherLayout,
            children: [
                { path: "", redirect: "/teacher/overview" },
                { path: "overview", component: TeacherOverview },
                { path: "classes", component: TeachingClasses },
                { path: "analysis", component: TeacherTeachingAnalysis },
                { path: "courses", component: TeacherCourseLibrary },
                { path: "generated-questions", component: TeacherGeneratedQuestions }
            ]
        },
        {
            path: "",
            component: Access
        },
        {
            path: "/test",
            component: ModuleTest
        },
        {
            path: "/xss",
            component: XssTest
        },
        {
            path: "/command",
            component: CommandTest
        },
        {
            path: "/xss-direct",
            component: XSSDirect
        }
    ]
});

router.beforeEach((to) => {
    if (isLabRunning.value && !to.path.startsWith("/user/module")) {
        const confirmed = window.confirm("实验正在进行中，离开页面前建议先结束实验。确定要继续离开吗？");
        if (!confirmed) {
            return false;
        }
    }

    const isProtectedRoute = to.path.startsWith("/teacher") || to.path.startsWith("/admin") || to.path.startsWith("/user");
    if (!isProtectedRoute) {
        return true;
    }

    const token = getStoredToken();
    if (!token) {
        return {
            path: "/",
            query: { redirect: to.fullPath },
        };
    }

    return getUserInfo(token)
        .then((response) => {
            if (!response?.data) {
                throw new Error(response?.message || "未获取到当前用户信息");
            }

            const currentUser = normalizeCurrentUser(response.data);
            if (!currentUser) {
                throw new Error("当前用户信息缺少角色字段");
            }

            storeAuthSession(token, currentUser);

            if (!to.path.startsWith("/teacher") && !to.path.startsWith("/admin")) {
                return true;
            }

            if (isPrivilegedRole(currentUser.role)) {
                return true;
            }

            return { path: "/user/profile" };
        })
        .catch((error) => {
            console.error("路由鉴权失败:", error);
            clearStoredAuthSession();
            return {
                path: "/",
                query: { redirect: to.fullPath },
            };
        });
});
