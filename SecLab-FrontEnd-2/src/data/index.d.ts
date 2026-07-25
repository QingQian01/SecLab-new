// 类型定义文件，为JavaScript模块提供类型

export interface ExperimentType {
  id: number;
  name: string;
  introduction: string;
  difficulty: number;
  taskPoints: Array<{
    id: number;
    name: string;
    description: string;
    score: number;
    document: string;
    questions?: any[];
  }>;
  targetMachine?: {
    id: string;
  };
}

// 声明模块导出
export const SQLInjectionExperiment: ExperimentType;
export const XSSExperiment: ExperimentType;
export const CSRFExperiment: ExperimentType;
export const CommandInjectionExperiment: ExperimentType;
export const FileUploadExperiment: ExperimentType;
export const MiddlewareVulnerabilityExperiment: ExperimentType;
export const ComponentVulnerabilityExperiment: ExperimentType;
export const StackOverflowExperiment: ExperimentType;
export const ProtocolAnalysisExperiment: ExperimentType;
export const HeapOverflowExperiment: ExperimentType;
export const FormatStringExperiment: ExperimentType;

export const AllExperiments: ExperimentType[];

// 辅助函数
export function findExperimentById(id: number): ExperimentType | undefined;
export const ExperimentTypes: {
  SQL_INJECTION: 1;
  XSS: 2;
  CSRF: 3;
  COMMAND_INJECTION: 4;
  FILE_UPLOAD: 5;
  MIDDLEWARE_VULNERABILITY: 6;
  COMPONENT_VULNERABILITY: 7;
  BUSINESS_LOGIC_VULNERABILITY: 8;
  INTRANET_PENETRATION: 9;
  CODE_AUDIT: 10;
  CTF_PRACTICE: 11;
  RED_TEAM_ARSENAL: 12;
  VULNERABILITY_METHODOLOGY: 13;
  STACK_OVERFLOW: 15;
  PROTOCOL_ANALYSIS: 16;
  HEAP_OVERFLOW: 17;
  FORMAT_STRING: 18;
};

export function getExperimentsByDifficulty(difficulty: number): ExperimentType[];
export function getBeginnerExperiments(): ExperimentType[];
export function getAdvancedExperiments(): ExperimentType[]; 