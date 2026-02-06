import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { format, startOfWeek, endOfWeek } from 'date-fns';
import {
  DocumentTextIcon,
  SparklesIcon,
  ClipboardDocumentIcon,
  CalendarDaysIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { Header } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, LoadingSpinner, Modal } from '../components/common';
import { useAuthStore, useReportStore, useTaskStore } from '../store';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

export function ReportsPage() {
  const { user } = useAuthStore();
  const { generateReport, isGenerating, generatedContent, clearGeneratedContent } = useReportStore();
  const { tasks: storeTasks } = useTaskStore();

  const [dateRange, setDateRange] = useState({
    start: format(startOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'),
    end: format(endOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'),
  });
  const [showReportModal, setShowReportModal] = useState(false);
  const [localTasks, setLocalTasks] = useState(storeTasks);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  // 날짜 범위 변경 시 tasks 로드
  useEffect(() => {
    const loadTasks = async () => {
      if (!user?.email) return;
      setIsLoadingTasks(true);
      try {
        const tasks = await api.getUserTimeline(user.email, dateRange.start, dateRange.end);
        setLocalTasks(tasks);
      } catch {
        setLocalTasks([]);
      } finally {
        setIsLoadingTasks(false);
      }
    };
    loadTasks();
  }, [user?.email, dateRange.start, dateRange.end]);

  const handleGenerateReport = async () => {
    if (!user?.email || !user?.name) {
      toast.error('로그인이 필요합니다');
      return;
    }

    if (localTasks.length === 0) {
      toast.error('해당 기간에 업무 데이터가 없습니다');
      return;
    }

    try {
      await generateReport({
        tasks: localTasks,
        startDate: dateRange.start,
        endDate: dateRange.end,
        writer: user.name,
        email: user.email,
      });
      setShowReportModal(true);
      toast.success('보고서가 생성되었습니다');
    } catch {
      toast.error('보고서 생성에 실패했습니다');
    }
  };

  const handleCopyReport = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent);
      toast.success('클립보드에 복사되었습니다');
    }
  };

  const handleDownloadReport = () => {
    if (generatedContent) {
      const blob = new Blob([generatedContent], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `weekly-report-${dateRange.start}-${dateRange.end}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('파일이 다운로드되었습니다');
    }
  };

  const handleCloseModal = () => {
    setShowReportModal(false);
    clearGeneratedContent();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title="보고서"
        subtitle="AI를 활용해 주간 보고서를 자동으로 생성하세요"
      />

      <main className="p-8">
        <div className="max-w-4xl mx-auto">
          {/* Report Generator Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="bg-gradient-to-br from-primary-600 to-primary-700 border-none mb-8">
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/20 mb-6">
                  <SparklesIcon className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  AI 보고서 생성
                </h2>
                <p className="text-primary-100 mb-6 max-w-md mx-auto">
                  연동된 플랫폼의 업무 데이터를 분석하여
                  <br />
                  자동으로 주간 보고서를 생성합니다
                </p>

                {/* Date Range Selector */}
                <div className="flex items-center justify-center gap-4 mb-6">
                  <div className="flex items-center gap-2 bg-white/10 rounded-lg px-4 py-2">
                    <CalendarDaysIcon className="w-5 h-5 text-white/70" />
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) =>
                        setDateRange((prev) => ({ ...prev, start: e.target.value }))
                      }
                      className="bg-transparent text-white border-none focus:outline-none text-sm"
                    />
                    <span className="text-white/50">~</span>
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) =>
                        setDateRange((prev) => ({ ...prev, end: e.target.value }))
                      }
                      className="bg-transparent text-white border-none focus:outline-none text-sm"
                    />
                  </div>
                </div>

                <Button
                  variant="secondary"
                  size="lg"
                  onClick={handleGenerateReport}
                  isLoading={isGenerating}
                  leftIcon={<SparklesIcon className="w-5 h-5" />}
                  className="shadow-lg"
                >
                  보고서 생성하기
                </Button>
              </div>
            </Card>
          </motion.div>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
          >
            {[
              {
                icon: DocumentTextIcon,
                title: '자동 분석',
                description: '업무 데이터를 자동으로 분석하여 핵심 내용을 추출합니다',
              },
              {
                icon: SparklesIcon,
                title: 'AI 요약',
                description: 'GPT 기반 AI가 업무 내용을 요약하고 정리합니다',
              },
              {
                icon: ClipboardDocumentIcon,
                title: '간편한 내보내기',
                description: '생성된 보고서를 복사하거나 파일로 다운로드할 수 있습니다',
              },
            ].map((feature, index) => (
              <Card key={index}>
                <div className="flex flex-col items-center text-center">
                  <div className="p-3 rounded-xl bg-primary-50 mb-4">
                    <feature.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-500">{feature.description}</p>
                </div>
              </Card>
            ))}
          </motion.div>

          {/* How it works */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>사용 방법</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    {
                      step: 1,
                      title: '기간 선택',
                      description: '보고서를 생성할 기간을 선택합니다 (기본값: 이번 주)',
                    },
                    {
                      step: 2,
                      title: '보고서 생성',
                      description: '버튼을 클릭하면 AI가 업무 데이터를 분석합니다',
                    },
                    {
                      step: 3,
                      title: '결과 확인',
                      description: '생성된 보고서를 확인하고 필요시 수정합니다',
                    },
                    {
                      step: 4,
                      title: '내보내기',
                      description: '보고서를 복사하거나 파일로 다운로드합니다',
                    },
                  ].map((item) => (
                    <div key={item.step} className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                        <span className="text-sm font-bold text-primary-700">{item.step}</span>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">{item.title}</h4>
                        <p className="text-sm text-gray-500">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Report Modal */}
        <Modal
          isOpen={showReportModal}
          onClose={handleCloseModal}
          title="생성된 보고서"
          size="full"
        >
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center py-16">
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-gray-500">보고서를 생성하고 있습니다...</p>
            </div>
          ) : generatedContent ? (
            <div>
              <div className="bg-gray-50 rounded-lg p-6 mb-6 max-h-[50vh] overflow-y-auto scrollbar-thin">
                <div className="prose prose-sm max-w-none markdown-content">
                  <ReactMarkdown>{generatedContent}</ReactMarkdown>
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={handleCopyReport}
                  leftIcon={<ClipboardDocumentIcon className="w-4 h-4" />}
                >
                  복사하기
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleDownloadReport}
                  leftIcon={<ArrowDownTrayIcon className="w-4 h-4" />}
                >
                  다운로드
                </Button>
                <Button onClick={handleCloseModal}>확인</Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">보고서 내용이 없습니다</p>
            </div>
          )}
        </Modal>
      </main>
    </div>
  );
}
