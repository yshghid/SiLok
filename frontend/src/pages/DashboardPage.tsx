import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { format, startOfWeek, endOfWeek, addDays } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  DocumentTextIcon,
  CalendarDaysIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  ArrowRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { Header } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, LoadingSpinner } from '../components/common';
import { useAuthStore, useTaskStore, useReportStore } from '../store';
import toast from 'react-hot-toast';

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { tasks, fetchTasks, isLoading: tasksLoading, dateRange } = useTaskStore();
  const { generateReport, isGenerating, generatedContent, clearGeneratedContent } = useReportStore();
  const [showReportModal, setShowReportModal] = useState(false);

  useEffect(() => {
    if (user?.email) {
      fetchTasks(user.email);
    }
  }, [user?.email, fetchTasks, dateRange]);

  const handleGenerateReport = async () => {
    if (!user?.email || !user?.name || tasks.length === 0) {
      toast.error('업무 데이터가 없습니다');
      return;
    }

    try {
      await generateReport({
        tasks,
        startDate: format(dateRange.start, 'yyyy-MM-dd'),
        endDate: format(dateRange.end, 'yyyy-MM-dd'),
        writer: user.name,
        email: user.email,
      });
      setShowReportModal(true);
      toast.success('보고서가 생성되었습니다');
    } catch {
      toast.error('보고서 생성에 실패했습니다');
    }
  };

  const stats = [
    {
      name: '이번 주 업무',
      value: tasks.length,
      icon: ClipboardDocumentListIcon,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
    },
    {
      name: '생성된 보고서',
      value: 3,
      icon: DocumentTextIcon,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
    },
    {
      name: '연동된 플랫폼',
      value: 4,
      icon: ChartBarIcon,
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
    },
  ];

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const start = startOfWeek(new Date(), { weekStartsOn: 1 });
    return addDays(start, i);
  });

  const getTaskCountForDate = (date: Date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return tasks.filter((t) => t.timestamp?.startsWith(dateStr)).length;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title={`안녕하세요, ${user?.name || '사용자'}님`}
        subtitle={format(new Date(), 'yyyy년 M월 d일 EEEE', { locale: ko })}
      />

      <main className="p-8">
        {/* Welcome banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card className="bg-gradient-to-r from-primary-600 to-primary-700 border-none">
            <div className="flex items-center justify-between p-6">
              <div className="text-white">
                <h2 className="text-2xl font-bold mb-2">주간 보고서를 생성해보세요</h2>
                <p className="text-primary-100 mb-4">
                  {format(dateRange.start, 'M월 d일')} - {format(dateRange.end, 'M월 d일')} 기간의 업무 데이터를 분석합니다
                </p>
                <Button
                  variant="secondary"
                  onClick={handleGenerateReport}
                  isLoading={isGenerating}
                  leftIcon={<SparklesIcon className="w-5 h-5" />}
                >
                  AI 보고서 생성
                </Button>
              </div>
              <div className="hidden md:block">
                <div className="w-32 h-32 bg-white/10 rounded-full flex items-center justify-center">
                  <DocumentTextIcon className="w-16 h-16 text-white/80" />
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                    <stat.icon className={`w-6 h-6 ${stat.textColor}`} />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Weekly Calendar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2"
          >
            <Card padding="none">
              <CardHeader className="px-6 py-4">
                <CardTitle subtitle={`${format(dateRange.start, 'M월 d일')} - ${format(dateRange.end, 'M월 d일')}`}>
                  이번 주 업무 현황
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/calendar')}
                  rightIcon={<ArrowRightIcon className="w-4 h-4" />}
                >
                  캘린더 보기
                </Button>
              </CardHeader>
              <CardContent className="px-6 pb-6">
                <div className="grid grid-cols-7 gap-2">
                  {weekDays.map((day) => {
                    const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
                    const taskCount = getTaskCountForDate(day);

                    return (
                      <div
                        key={day.toISOString()}
                        className={`p-3 rounded-xl text-center transition-all ${
                          isToday
                            ? 'bg-primary-50 border-2 border-primary-200'
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <p className={`text-xs font-medium ${isToday ? 'text-primary-600' : 'text-gray-500'}`}>
                          {format(day, 'EEE', { locale: ko })}
                        </p>
                        <p className={`text-lg font-bold mt-1 ${isToday ? 'text-primary-700' : 'text-gray-900'}`}>
                          {format(day, 'd')}
                        </p>
                        {taskCount > 0 && (
                          <Badge variant={isToday ? 'primary' : 'gray'} className="mt-2">
                            {taskCount}건
                          </Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Tasks */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card padding="none">
              <CardHeader className="px-6 py-4">
                <CardTitle>최근 업무</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/tasks')}
                  rightIcon={<ArrowRightIcon className="w-4 h-4" />}
                >
                  전체 보기
                </Button>
              </CardHeader>
              <CardContent className="px-6 pb-6">
                {tasksLoading ? (
                  <div className="flex justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : tasks.length === 0 ? (
                  <div className="text-center py-8">
                    <ClipboardDocumentListIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">업무 데이터가 없습니다</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.slice(0, 5).map((task, index) => (
                      <div
                        key={task.task_id || index}
                        className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                          <CalendarDaysIcon className="w-4 h-4 text-primary-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 line-clamp-2">{task.content}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {task.sender} • {task.timestamp ? format(new Date(task.timestamp), 'M/d HH:mm') : ''}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Report Modal */}
        {showReportModal && generatedContent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[80vh] overflow-hidden"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">생성된 보고서</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowReportModal(false);
                    clearGeneratedContent();
                  }}
                >
                  닫기
                </Button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="prose prose-sm max-w-none markdown-content">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                    {generatedContent}
                  </pre>
                </div>
              </div>
              <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
                <Button variant="secondary" onClick={() => navigator.clipboard.writeText(generatedContent)}>
                  복사하기
                </Button>
                <Button onClick={() => navigate('/reports')}>보고서 목록으로</Button>
              </div>
            </motion.div>
          </div>
        )}
      </main>
    </div>
  );
}
