import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import { Header } from '../components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  Button,
  Input,
  LoadingSpinner,
  PlatformBadge,
} from '../components/common';
import { useAuthStore, useTaskStore } from '../store';

const platformFilters = [
  { value: '', label: '전체' },
  { value: 'slack', label: 'Slack' },
  { value: 'notion', label: 'Notion' },
  { value: 'onedrive', label: 'OneDrive' },
  { value: 'outlook', label: 'Outlook' },
];

export function TasksPage() {
  const { user } = useAuthStore();
  const {
    filteredTasks,
    isLoading,
    dateRange,
    setDateRange,
    setFilter,
    fetchTasks,
    filter,
  } = useTaskStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('');

  useEffect(() => {
    if (user?.email) {
      fetchTasks(user.email);
    }
  }, [user?.email, fetchTasks, dateRange]);

  useEffect(() => {
    setFilter({
      ...filter,
      search: searchTerm,
      platform: selectedPlatform || undefined,
    });
  }, [searchTerm, selectedPlatform]);

  const handleRefresh = () => {
    if (user?.email) {
      fetchTasks(user.email);
    }
  };

  const handleDateChange = (type: 'start' | 'end', value: string) => {
    setDateRange({
      ...dateRange,
      [type]: new Date(value),
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title="업무 목록"
        subtitle="연동된 플랫폼의 업무 데이터를 확인하세요"
      />

      <main className="p-8">
        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <Card>
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <Input
                  placeholder="업무 내용 또는 발신자로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  leftIcon={<MagnifyingGlassIcon className="w-5 h-5" />}
                />
              </div>

              {/* Date Range */}
              <div className="flex items-center gap-2">
                <CalendarDaysIcon className="w-5 h-5 text-gray-400" />
                <input
                  type="date"
                  value={format(dateRange.start, 'yyyy-MM-dd')}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <span className="text-gray-400">~</span>
                <input
                  type="date"
                  value={format(dateRange.end, 'yyyy-MM-dd')}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {/* Platform Filter */}
              <div className="flex items-center gap-2">
                <FunnelIcon className="w-5 h-5 text-gray-400" />
                <select
                  value={selectedPlatform}
                  onChange={(e) => setSelectedPlatform(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                >
                  {platformFilters.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Refresh */}
              <Button
                variant="secondary"
                onClick={handleRefresh}
                leftIcon={<ArrowPathIcon className="w-4 h-4" />}
              >
                새로고침
              </Button>
            </div>
          </Card>
        </motion.div>

        {/* Tasks Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card padding="none">
            <CardHeader className="px-6 py-4">
              <CardTitle subtitle={`총 ${filteredTasks.length}건`}>
                업무 리스트
              </CardTitle>
            </CardHeader>

            {isLoading ? (
              <div className="flex justify-center py-16">
                <LoadingSpinner size="lg" />
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="text-center py-16">
                <MagnifyingGlassIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">검색 결과가 없습니다</p>
                <p className="text-sm text-gray-400">
                  다른 검색어나 필터를 사용해보세요
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        플랫폼
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        업무 내용
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        발신자
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        수신자
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        일시
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredTasks.map((task, index) => (
                      <motion.tr
                        key={task.task_id || index}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: index * 0.02 }}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <PlatformBadge platform={task.platform || 'unknown'} />
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-900 line-clamp-2 max-w-md">
                            {task.content}
                          </p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-700">{task.sender}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-500">{task.receiver || '-'}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-500">
                            {task.timestamp
                              ? format(new Date(task.timestamp), 'M월 d일 HH:mm', { locale: ko })
                              : '-'}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
