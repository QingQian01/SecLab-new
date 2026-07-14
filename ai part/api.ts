import axios from "axios";
import type { RegisterForm } from "./types/auth";
import type { User } from "./types/user";
import type { ModuleOverViewType } from "./pages/User/Modules/components/ModuleOverView";
import type { Course } from "./pages/User/Course/index.ts";
import { CourseStatus } from "./pages/User/Course/index.ts";
import type { Module } from "./pages/User/Module/index.ts";
import { findExperimentById } from './data';

// 可配置的API基础URL
// 优先使用环境变量，如果没有则使用默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8083";
// Docker API服务器的URL
const DOCKER_API_URL = import.meta.env.VITE_DOCKER_API_URL || "http://localhost:3000";
console.log('API基础URL:', API_BASE_URL);
console.log('Docker API URL:', DOCKER_API_URL);

const BASE_URL: string = API_BASE_URL;
const IMAGE_URL = `${BASE_URL}/images/view/`;

type Result<T> = {
    isSuccess:number,
    status:number,
    message:string,
    data:T
}

// 定义后端返回的课程数据类型
export interface CourseSummaryDto {
    id: number;
    name: string;
    description: string;
    difficulty: number;
    imageUrl: string;
    type: string;
    tags: string[];
    status: string;
}

export let image = (imageName: string | null | undefined) => {
    // 添加空值检查
    if (!imageName) {
        return '/default-course-image.png'; // 默认图片路径
    }
    
    // 如果已经是完整URL，直接返回
    if (imageName.startsWith('http://') || imageName.startsWith('https://')) {
        return imageName;
    }
    
    // 如果是本地文件路径，直接从public目录加载
    if (imageName.startsWith('/') || imageName.includes('.png') || imageName.includes('.jpg') || imageName.includes('.jpeg') || imageName.includes('.svg')) {
        // 尝试从public目录加载
        try {
            // 移除可能的UUID前缀 (类似 "a9fe8e50-ba21-45ef-abd5-50b717857502-1.SQL注入攻防实战.png")
            const fileName = imageName.includes('-') ? imageName.split('-').pop() : imageName;
            // 如果文件名包含路径分隔符，只取最后一部分
            const cleanFileName = fileName?.includes('/') ? fileName.split('/').pop() : fileName;
            
            if (cleanFileName) {
                return `/${cleanFileName}`;
            }
        } catch (e) {
            console.warn('处理图片路径出错:', e);
        }
    }
    
    // 拼接后端图片URL
    return IMAGE_URL + imageName;
};

// 预设的测试账号，修改为let使其可变
let TEST_ACCOUNTS: Array<{
    userStudentNumber: string;
    userPassword: string;
    userId: number;
    userImage: string;
    userName: string;
    classId: number;
    token: string;
    userEmail?: string;
    userTel?: string;
    userGender?: number;
    userAcademy?: string;
    userClass?: string;
}> = [
    {
        userStudentNumber: "admin",
        userPassword: "admin",
        userId: 1,
        userImage: "/1.SQL注入攻防实战.png",
        userName: "管理员",
        classId: 1,
        token: "admin-token-12345",
        userEmail: "admin@example.com",
        userTel: "13800138000",
        userGender: 1,
        userAcademy: "网络安全学院",
        userClass: "网络安全232班"
    },
    {
        userStudentNumber: "test",
        userPassword: "test",
        userId: 2,
        userImage: "/2.XSS漏洞深度解析.png",
        userName: "测试用户",
        classId: 1,
        token: "test-token-67890",
        userEmail: "test@example.com",
        userTel: "13800138000",
        userGender: 1,
        userAcademy: "网络安全学院",
        userClass: "网络安全232班"
    },
    {
        userStudentNumber: "student",
        userPassword: "student",
        userId: 3,
        userImage: "/3.文件上传漏洞突破.png",
        userName: "学生用户",
        classId: 2,
        token: "student-token-abcde",
        userEmail: "student@example.com",
        userTel: "13800138000",
        userGender: 1,
        userAcademy: "网络安全学院",
        userClass: "网络安全232班"
    }
];

// 添加localStorage持久化支持
const saveAccountsToLocalStorage = () => {
    localStorage.setItem('seclab_accounts', JSON.stringify(TEST_ACCOUNTS));
};

const loadAccountsFromLocalStorage = () => {
    const savedAccounts = localStorage.getItem('seclab_accounts');
    if (savedAccounts) {
        try {
            TEST_ACCOUNTS = JSON.parse(savedAccounts);
            console.log('从localStorage加载了用户账号:', TEST_ACCOUNTS.length);
        } catch (e) {
            console.error('解析localStorage中的账号数据失败:', e);
        }
    }
};

// 初始化时加载已保存的账号
loadAccountsFromLocalStorage();

export async function login(loginRequest: { userStudentNumber: string; userPassword: string; }): Promise<Result<{ 
    loginData: {
        userId: number; 
        userStudentNumber: string; 
        userImage: string; 
        userName: string; 
        classId: number; 
        token: string; 
    }
}>> {
    try {
        console.log('发送登录请求:', loginRequest);
        // Make a POST request to the login endpoint with the loginRequest data
        const response = await axios.post(`${BASE_URL}/stu/login`, loginRequest);
        console.log('登录响应原始数据:', response);

        // Return the response data (e.g., user info, tokens, etc.)
        return response.data;
    } catch (error) {
        console.error('登录请求异常，使用本地登录机制:', error);
        
        // 使用本地登录机制
        const testAccount = TEST_ACCOUNTS.find(
            account => account.userStudentNumber === loginRequest.userStudentNumber && 
                      account.userPassword === loginRequest.userPassword
        );
        
        if (testAccount) {
            console.log('登录成功:', testAccount.userName);
            return {
                isSuccess: 1,
                status: 200,
                message: "登录成功",
                data: {
                    loginData: {
                        userId: testAccount.userId,
                        userStudentNumber: testAccount.userStudentNumber,
                        userImage: testAccount.userImage,
                        userName: testAccount.userName,
                        classId: testAccount.classId,
                        token: testAccount.token
                    }
                }
            };
        }
        
        // 如果账号不匹配，返回登录失败
        return {
            isSuccess: 0,
            status: 401,
            message: "登录失败：用户名或密码错误",
            data: null
        } as any;
    }
}

export async function register(registerRequest: RegisterForm): Promise<Result<undefined>> {
    try {
        console.log('发送注册请求:', registerRequest);
        // Make a POST request to the register endpoint with the registerRequest data
        const response = await axios.post(`${BASE_URL}/stu/register`, registerRequest);
        console.log('注册响应原始数据:', response);
        
        // Return the response data
        return response.data;
    } catch (error) {
        console.error('注册请求异常，使用本地注册机制:', error);
        
        // 检查学号是否已存在
        const existingAccount = TEST_ACCOUNTS.find(
            account => account.userStudentNumber === registerRequest.userStudentNumber
        );
        
        if (existingAccount) {
            return {
                isSuccess: 0,
                status: 400,
                message: "注册失败：学号已存在",
                data: undefined
            };
        }
        
        try {
            // 创建新用户
            const newUserId = Math.max(...TEST_ACCOUNTS.map(acc => acc.userId)) + 1;
            const newToken = `user-token-${Date.now()}`;
            const avatarIndex = (newUserId % 5) + 1;
            const defaultImage = `/${avatarIndex}.SQL注入攻防实战.png`;
            
            // 确保性别是数字类型
            const userGender = typeof registerRequest.userGender === 'number' ? 
                registerRequest.userGender : 
                registerRequest.userGender === '1' || registerRequest.userGender === '男' ? 1 : 0;
            
            console.log('处理注册性别数据:', {
                原始值: registerRequest.userGender,
                类型: typeof registerRequest.userGender,
                转换后: userGender
            });
            
            // 使用用户提供的学院和班级，如果没有则使用默认值
            const userAcademy = registerRequest.userAcademy || "网络安全学院";
            const userClass = registerRequest.userClass || "网络安全232班";
            
            const newUser = {
                userStudentNumber: registerRequest.userStudentNumber,
                userPassword: registerRequest.userPassword,
                userId: newUserId,
                userImage: registerRequest.userImage || defaultImage, // 如果用户上传了头像，则使用用户的头像
                userName: registerRequest.userName,
                userEmail: registerRequest.userEmail || `${registerRequest.userStudentNumber}@example.com`,
                userTel: registerRequest.userTel || "13800138000",
                userGender: userGender,
                classId: registerRequest.classId || 1,
                token: newToken,
                userAcademy: userAcademy,
                userClass: userClass
            };
            
            console.log('创建新用户:', newUser);
            TEST_ACCOUNTS.push(newUser);
            saveAccountsToLocalStorage();
            
            return {
                isSuccess: 1,
                status: 200,
                message: "注册成功",
                data: undefined
            };
        } catch (e) {
            console.error('本地注册处理错误:', e);
            return {
                isSuccess: 0,
                status: 500,
                message: "注册处理失败",
            data: undefined
        };
        }
    }
}

export async function getUserInfo(token: string): Promise<Result<User>> {
    try {
        console.log('调用getUserInfo API，token:', token);
        const response = await axios.get(`${BASE_URL}/stu/profile?token=${token}`);
        console.log('getUserInfo API响应:', response);
        
        if (response.status === 200) {
            // Return the response data (e.g., user info, tokens, etc.)
            return response.data;
        } else {
            // Handle unexpected response status
            throw new Error(`Unexpected response status: ${response.status}`);
        }
    } catch (error) {
        console.error('获取用户信息失败，使用本地数据:', error);
        
        // 查找匹配的测试账号
        console.log('查找token匹配的测试账号:', token);
        console.log('当前测试账号列表:', TEST_ACCOUNTS);
        
        const testAccount = TEST_ACCOUNTS.find(account => account.token === token);
        console.log('找到匹配的测试账号:', testAccount);
        
        if (testAccount) {
            // 确保性别信息是数字类型
            const userGender = typeof testAccount.userGender === 'number' ? testAccount.userGender : 1;
            
            // 返回用户的所有信息，确保包含学院和班级
            console.log('获取到用户信息:', {
                userId: testAccount.userId,
                userName: testAccount.userName,
                userStudentNumber: testAccount.userStudentNumber,
                userGender: userGender,
                userAcademy: testAccount.userAcademy,
                userClass: testAccount.userClass
            });
            
            // 构建完整的用户对象
            const userData = {
                userId: testAccount.userId,
                userStudentNumber: testAccount.userStudentNumber,
                userImage: testAccount.userImage,
                userName: testAccount.userName,
                classId: testAccount.classId,
                userEmail: testAccount.userEmail || `${testAccount.userStudentNumber}@example.com`,
                userTel: testAccount.userTel || "13800138000",
                userGender: userGender,
                userAcademy: testAccount.userAcademy || "网络安全学院",
                userClass: testAccount.userClass || "网络安全232班"
            };
            
            console.log('返回完整的用户数据:', userData);
            
            return {
                isSuccess: 1,
                status: 200,
                message: "获取用户信息成功",
                data: userData
            };
        }
        
        console.error('未找到匹配的账号，token:', token);
        throw new Error('获取用户信息失败，且无匹配的账号');
    }
}

// 添加更新用户信息的本地实现
export async function updateUserInfoByToken(user: User, token: string): Promise<Result<User>> {
    try {
        const response = await axios.post(`${BASE_URL}/stu/updateProfile?token=${token}`, user);
            return response.data;
    } catch (error) {
        console.error('更新用户信息失败，使用本地更新:', error);
        
        // 查找匹配的账号
        const userIndex = TEST_ACCOUNTS.findIndex(account => account.token === token);
        
        if (userIndex !== -1) {
            // 更新用户信息
            TEST_ACCOUNTS[userIndex].userName = user.userName || TEST_ACCOUNTS[userIndex].userName;
            if (user.userImage) TEST_ACCOUNTS[userIndex].userImage = user.userImage;
            
            // 保存到localStorage
            saveAccountsToLocalStorage();
            
            // 返回完整的用户信息，包括学院和班级
            return {
                isSuccess: 1,
                status: 200,
                message: "更新用户信息成功",
                data: {
                    ...user,
                    userAcademy: user.userAcademy || "网络安全学院",
                    userClass: user.userClass || "网络安全232班"
                }
            };
        }
        
        return {
            isSuccess: 0,
            status: 404,
            message: "更新失败：找不到用户",
            data: null
        } as any;
    }
}

export async function getModuleList(): Promise<Result<ModuleOverViewType[]>> {
    const response = await axios.post(`${BASE_URL}/stu/module/modules`);
    if (response.status === 200) {
        // Return the response data (e.g., updated user info)
        return response.data;
    } else {
        // Handle unexpected response status
        throw new Error(`Unexpected response status: ${response.status}`);
    }
}

export async function getCourseList(): Promise<Result<CourseSummaryDto[]>> {
    const response = await axios.get(`${BASE_URL}/course/overview-list`);
    if (response.status === 200) {
        return response.data;
    } else {
        throw new Error(`Unexpected response status: ${response.status}`);
    }
}   

export async function getCourseDetail(id:number): Promise<Result<Course>> {
    try {
        const response = await axios.get(`${BASE_URL}/course/detail?id=${id}`);
        if (response.status === 200) {
            return response.data;
        } else {
            console.error(`Unexpected response status: ${response.status}`);
            return getFallbackCourseDetail(id);
        }
    } catch (error) {
        console.error('Error fetching course detail:', error);
        return getFallbackCourseDetail(id);
    }
}

// 提供硬编码的备用课程数据
function getFallbackCourseDetail(id: number): Result<Course> {
    // 使用SQL文件中的课程数据作为备用
    const fallbackCourses = [
        {
            id: 1,
            name: "SQL注入攻击",
            description: "本课程详细讲解SQL注入攻击的原理、分类和防御技术。通过实际案例演示如何发现和利用SQL注入漏洞，以及如何通过参数化查询、输入验证和最小权限原则等方法防止SQL注入攻击，保障Web应用的数据安全。",
            difficulty: 3,
            imageUrl: "a9fe8e50-ba21-45ef-abd5-50b717857502-1.SQL注入攻防实战.png",
            instructor: "张教授",
            costTime: 8,
            schedule: "每周一",
            status: CourseStatus.ACTIVE,
            tags: ["SQL注入", "Web安全", "数据库安全"],
            type: "web",
            modules: []
        },
        {
            id: 2,
            name: "XSS与CSRF攻击",
            description: "本课程深入剖析跨站脚本(XSS)和跨站请求伪造(CSRF)攻击的原理和防御方法。通过实例演示反射型XSS、存储型XSS和DOM型XSS攻击，以及CSRF攻击的实施过程，帮助学习者掌握Web前端安全防护的关键技术。",
            difficulty: 2,
            imageUrl: "eb678908-4878-4303-94ae-b3434d52612a-2.XSS漏洞深度解析.png",
            instructor: "李教授",
            costTime: 6,
            schedule: "每周二",
            status: CourseStatus.ACTIVE,
            tags: ["XSS", "CSRF", "Web安全"],
            type: "web",
            modules: []
        },
        {
            id: 3,
            name: "IDS和IPS系统",
            description: "本课程介绍入侵检测系统(IDS)和入侵防御系统(IPS)的工作原理和部署策略。通过分析网络流量和系统行为，识别和防御各类网络攻击，包括异常检测、特征匹配和行为分析等技术，帮助学习者构建有效的网络安全防护体系。",
            difficulty: 3,
            imageUrl: "5780e906-42a1-4a88-ad06-d054bbf92735-3.文件上传漏洞突破.png",
            instructor: "王教授",
            costTime: 7,
            schedule: "每周三",
            status: CourseStatus.ACTIVE,
            tags: ["IDS", "IPS", "网络安全"],
            type: "network",
            modules: []
        },
        {
            id: 4,
            name: "APT攻击分析",
            description: "本课程深入分析高级持续性威胁(APT)攻击的特点和防御策略。通过实际APT攻击案例分析，介绍攻击者的战术、技术和程序(TTP)，以及如何建立有效的威胁情报和安全防御体系，提升组织抵御高级威胁的能力。",
            difficulty: 4,
            imageUrl: "4.中间件漏洞利用.png",
            instructor: "赵教授",
            costTime: 10,
            schedule: "每周四",
            status: CourseStatus.ACTIVE,
            tags: ["APT", "高级威胁", "网络安全"],
            type: "advanced",
            modules: []
        },
        {
            id: 5,
            name: "防火墙技术",
            description: "本课程详细讲解网络防火墙的原理、类型和配置方法。包括包过滤防火墙、状态检测防火墙、应用层防火墙和下一代防火墙的特点与部署策略，以及访问控制列表(ACL)、NAT配置、VPN集成等实用技术，帮助学习者掌握网络边界防护的核心技能。",
            difficulty: 3,
            imageUrl: "5.组件漏洞挖掘.png",
            instructor: "钱教授",
            costTime: 8,
            schedule: "每周五",
            status: CourseStatus.ACTIVE,
            tags: ["防火墙", "网络安全", "边界防护"],
            type: "network",
            modules: []
        },
        {
            id: 6,
            name: "古典密码学",
            description: "本课程介绍密码学的历史发展和古典密码体系，包括替换密码、置换密码、维吉尼亚密码等经典加密方法的原理与分析。通过历史案例和实际操作，了解密码破译的基本方法和密码学的基本概念，为现代密码学学习奠定基础。",
            difficulty: 2,
            imageUrl: "6.框架漏洞利用.png",
            instructor: "孙教授",
            costTime: 6,
            schedule: "每周一",
            status: CourseStatus.ACTIVE,
            tags: ["密码学", "古典密码", "信息安全"],
            type: "crypto",
            modules: []
        },
        {
            id: 7,
            name: "公钥密码简介",
            description: "本课程详细讲解公钥密码体系的基本原理和应用场景。介绍非对称加密的数学基础、密钥管理、数字证书和PKI体系，以及RSA、ECC等常用公钥算法的工作机制，帮助学习者理解现代密码学中最重要的概念和技术。",
            difficulty: 3,
            imageUrl: "7.业务逻辑漏洞实战.png",
            instructor: "周教授",
            costTime: 8,
            schedule: "每周二",
            status: CourseStatus.ACTIVE,
            tags: ["公钥密码", "非对称加密", "密码学"],
            type: "crypto",
            modules: []
        },
        {
            id: 8,
            name: "RSA公钥加密方案",
            description: "本课程深入剖析RSA公钥加密算法的数学原理、实现细节和安全性分析。包括素数生成、密钥生成、加密解密过程、数字签名应用，以及常见攻击方法和防御措施，帮助学习者全面掌握这一最广泛使用的公钥密码系统。",
            difficulty: 4,
            imageUrl: "8.内网渗透技术.png",
            instructor: "吴教授",
            costTime: 9,
            schedule: "每周三",
            status: CourseStatus.ACTIVE,
            tags: ["RSA", "公钥密码", "密码学"],
            type: "crypto",
            modules: []
        },
        {
            id: 9,
            name: "数字签名技术",
            description: "本课程详细介绍数字签名的原理、算法和应用。包括RSA签名、DSA、ECDSA等签名算法的工作机制，数字证书与PKI体系，以及时间戳、盲签名等高级签名技术，帮助学习者理解数字签名在信息安全中的重要作用和实现方法。",
            difficulty: 4,
            imageUrl: "9.代码审计进阶.png",
            instructor: "郑教授",
            costTime: 8,
            schedule: "每周四",
            status: CourseStatus.ACTIVE,
            tags: ["数字签名", "PKI", "密码学"],
            type: "crypto",
            modules: []
        },
        {
            id: 10,
            name: "操作系统安全概述",
            description: "本课程全面介绍操作系统安全的核心概念和防护技术。包括访问控制、权限管理、认证机制、内核安全、内存保护等基础安全机制，以及常见操作系统的安全配置和加固方法，帮助学习者建立系统安全的整体认识。",
            difficulty: 3,
            imageUrl: "10.CTF攻防实战.png",
            instructor: "王教授",
            costTime: 7,
            schedule: "每周五",
            status: CourseStatus.ACTIVE,
            tags: ["操作系统安全", "系统安全", "访问控制"],
            type: "system",
            modules: []
        },
        {
            id: 11,
            name: "可信计算技术",
            description: "本课程深入讲解可信计算的基本原理和关键技术。包括可信平台模块(TPM)、可信启动、远程证明、密封存储等可信计算机制，以及可信计算在云计算、物联网等领域的应用，帮助学习者理解构建可信系统的方法和挑战。",
            difficulty: 4,
            imageUrl: "11.红队武器库.png",
            instructor: "李教授",
            costTime: 9,
            schedule: "每周一",
            status: CourseStatus.ACTIVE,
            tags: ["可信计算", "系统安全", "TPM"],
            type: "system",
            modules: []
        },
        {
            id: 12,
            name: "网络安全概述",
            description: "本课程全面介绍网络安全的基本概念、威胁类型和防护策略。包括网络攻击分类、网络协议安全、边界防护、入侵检测与防御、安全运维等核心内容，帮助学习者建立网络安全的整体认识和防护思路。",
            difficulty: 3,
            imageUrl: "12.漏洞挖掘方法论.png",
            instructor: "张教授",
            costTime: 8,
            schedule: "每周二",
            status: CourseStatus.ACTIVE,
            tags: ["网络安全", "安全架构", "威胁防护"],
            type: "network",
            modules: []
        }
    ];
    
    // 查找请求的ID，如果找不到则返回第一个课程
    const course = fallbackCourses.find(c => c.id === id) || fallbackCourses[0];
    
    return {
        isSuccess: 1,
        status: 200,
        message: "success",
        data: course as Course
    };
}

export interface EventsIngestPayload {
    batch_id: string
    source_system: string
    generated_at: string
    user_context: {
        user_id: number
        class_id: number
        course_id: number
        module_id: number
        task_id: number | null
        question_id: number | null
        lab_session_id: string
    }
    events: Array<{
        event_id: string
        request_id?: string
        event_type: string
        event_time: string
        user_id: number
        class_id: number
        course_id: number
        module_id: number
        task_id?: number | null
        question_id?: number | null
        lab_session_id: string
        source: string
        question_type?: string | null
        answer?: string | string[] | null
        standard_answer?: string | null
        question_score?: number | null
        cost_time?: number | null
        is_correct?: boolean | null
        container_name?: string | null
        flag_text?: string | null
        score?: number | null
        command_id?: string | null
        command?: string | null
        cwd?: string | null
        exit_code?: number | null
        duration_ms?: number | null
        output_digest?: string | null
        file_path?: string | null
        file_ext?: string | null
        action?: string | null
        size_before?: number | null
        size_after?: number | null
        is_key_file?: boolean | null
        error_signature?: string | null
        error_category?: string | null
        raw_excerpt?: string | null
        severity?: string | null
        extra?: Record<string, any>
    }>
    ai_generated_questions?: Array<unknown>
    profile_rebuild?: {
        user_id: number
        class_id: number
        rebuild_after_ingest: boolean
    }
}

export async function ingestEvents(payload: EventsIngestPayload): Promise<Result<unknown>> {
    const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || "http://localhost:8010";
    try {
        const response = await axios.post(`${AGENT_BASE_URL}/api/external/events/ingest`, payload, {
            headers: { 'Content-Type': 'application/json' }
        })
        console.log('[EventsIngest] 成功:', response.data)
        return response.data
    } catch (error) {
        console.error('[EventsIngest] 失败:', error)
        return { isSuccess: 0, status: 500, message: '事件上报失败', data: null }
    }
}

export async function getModuleDetail(id:number): Promise<Result<Module>> {
    try {
        const response = await axios.get(`${BASE_URL}/course/module/detail?id=${id}`);
        if (response.status === 200) {
            return response.data;
        } else {
            console.error(`Unexpected response status: ${response.status}`);
            return getFallbackModuleDetail(id);
        }
    } catch (error) {
        console.error('Error fetching module detail:', error);
        return getFallbackModuleDetail(id);
    }
}   

// 提供硬编码的备用模块数据
function getFallbackModuleDetail(id: number): Result<Module> {
    // 尝试从我们的备用数据中查找对应ID的实验
    const experiment = findExperimentById(Number(id));
    
    if (experiment) {
        // 确保experiment的结构符合Module接口
        const moduleData = {
            id: experiment.id,
            name: experiment.name,
            introduction: experiment.introduction,
            difficulty: experiment.difficulty,
            taskPoints: experiment.taskPoints.map(task => ({
                ...task,
                questions: task.questions || []
            })),
            targetMachine: experiment.targetMachine
        };
        
        return {
            isSuccess: 1,
            status: 200,
            message: "success",
            data: moduleData as any
        };
    } else {
        // 如果找不到对应ID的实验，返回默认的SQL注入实验（ID为1）
        const defaultExperiment = findExperimentById(1);
        const moduleData = {
            id: id, // 使用请求的ID
            name: defaultExperiment?.name || "SQL注入基础实验",
            introduction: defaultExperiment?.introduction || "SQL注入基础实验介绍",
            difficulty: defaultExperiment?.difficulty || 3,
            taskPoints: (defaultExperiment?.taskPoints || []).map(task => ({
                ...task,
                questions: task.questions || []
            })),
            targetMachine: defaultExperiment?.targetMachine || { id: "default-machine" }
        };
        
        return {
            isSuccess: 1,
            status: 200,
            message: "success",
            data: moduleData as any
        };
    }
}

