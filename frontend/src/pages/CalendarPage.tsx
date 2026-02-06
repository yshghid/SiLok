import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addMonths,
  subMonths,
  isSameMonth,
  isSameDay,
  isToday,
} from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import { Header } from '../components/layout';
import { Card, CardHeader, CardTitle, Button, Badge, LoadingSpinner } from '../components/common';
import { useAuthStore, useTaskStore } from '../store';
import { Task } from '../types';
import { clsx } from 'clsx';

export function CalendarPage() {
  const { user } = useAuthStore();
  const { tasks, fetchTasks, isLoading, setDateRange } = useTaskStore();
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

  useEffect(() => {
    if (user?.email) {
      const start = startOfMonth(currentMonth);
      const end = endOfMonth(currentMonth);
      setDateRange({ start, end });
      fetchTasks(user.email);
    }
  }, [user?.email, currentMonth, fetchTasks, setDateRange]);

  const tasksByDate = useMemo(() => {
    const map = new Map<string, Task[]>();
    tasks.forEach((task) => {
      if (task.timestamp) {
        const dateKey = format(new Date(task.timestamp), 'yyyy-MM-dd');
        const existing = map.get(dateKey) || [];
        map.set(dateKey, [...existing, task]);
      }
    });
    return map;
  }, [tasks]);

  const selectedDateTasks = useMemo(() => {
    if (!selectedDate) return [];
    const dateKey = format(selectedDate, 'yyyy-MM-dd');
    return tasksByDate.get(dateKey) || [];
  }, [selectedDate, tasksByDate]);

  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 0 });
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 0 });

    const days: Date[] = [];
    let day = startDate;
    while (day <= endDate) {
      days.push(day);
      day = addDays(day, 1);
    }
    return days;
  }, [currentMonth]);

  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentMonth((prev) =>
      direction === 'prev' ? subMonths(prev, 1) : addMonths(prev, 1)
    );
  };

  const handleDateClick = (date: Date) => {
    setSelectedDate(date);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title="캘린더"
        subtitle="업무 일정을 한눈에 확인하세요"
      />

      <main className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-2"
          >
            <Card padding="none">
              {/* Calendar Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h2 className="text-xl font-bold text-gray-900">
                  {format(currentMonth, 'yyyy년 M월', { locale: ko })}
                </h2>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigateMonth('prev')}
                    className="p-2"
                  >
                    <ChevronLeftIcon className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentMonth(new Date())}
                  >
                    오늘
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigateMonth('next')}
                    className="p-2"
                  >
                    <ChevronRightIcon className="w-5 h-5" />
                  </Button>
                </div>
              </div>

              {/* Week Days Header */}
              <div className="grid grid-cols-7 border-b border-gray-100">
                {weekDays.map((day, index) => (
                  <div
                    key={day}
                    className={clsx(
                      'px-4 py-3 text-center text-sm font-semibold',
                      index === 0 ? 'text-red-500' : index === 6 ? 'text-blue-500' : 'text-gray-600'
                    )}
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Grid */}
              {isLoading ? (
                <div className="flex justify-center py-20">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <div className="grid grid-cols-7">
                  {calendarDays.map((day, index) => {
                    const dateKey = format(day, 'yyyy-MM-dd');
                    const dayTasks = tasksByDate.get(dateKey) || [];
                    const isCurrentMonth = isSameMonth(day, currentMonth);
                    const isSelected = selectedDate && isSameDay(day, selectedDate);
                    const isTodayDate = isToday(day);
                    const dayOfWeek = day.getDay();

                    return (
                      <motion.button
                        key={dateKey}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: index * 0.005 }}
                        onClick={() => handleDateClick(day)}
                        className={clsx(
                          'relative min-h-[100px] p-2 border-b border-r border-gray-100 transition-colors text-left',
                          isCurrentMonth ? 'bg-white' : 'bg-gray-50',
                          isSelected && 'bg-primary-50 ring-2 ring-primary-500 ring-inset',
                          !isSelected && 'hover:bg-gray-50'
                        )}
                      >
                        <span
                          className={clsx(
                            'inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-medium',
                            !isCurrentMonth && 'text-gray-400',
                            isCurrentMonth && dayOfWeek === 0 && 'text-red-500',
                            isCurrentMonth && dayOfWeek === 6 && 'text-blue-500',
                            isCurrentMonth && dayOfWeek > 0 && dayOfWeek < 6 && 'text-gray-900',
                            isTodayDate && 'bg-primary-600 text-white'
                          )}
                        >
                          {format(day, 'd')}
                        </span>

                        {/* Task indicators */}
                        {dayTasks.length > 0 && (
                          <div className="mt-1 space-y-1">
                            {dayTasks.slice(0, 2).map((task, i) => (
                              <div
                                key={i}
                                className="text-xs px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded truncate"
                              >
                                {task.content.substring(0, 15)}...
                              </div>
                            ))}
                            {dayTasks.length > 2 && (
                              <p className="text-xs text-gray-500 px-1.5">
                                +{dayTasks.length - 2} more
                              </p>
                            )}
                          </div>
                        )}
                      </motion.button>
                    );
                  })}
                </div>
              )}
            </Card>
          </motion.div>

          {/* Selected Date Tasks */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card padding="none">
              <CardHeader className="px-6 py-4">
                <CardTitle
                  subtitle={
                    selectedDate
                      ? format(selectedDate, 'M월 d일 EEEE', { locale: ko })
                      : '날짜를 선택하세요'
                  }
                >
                  <div className="flex items-center gap-2">
                    <CalendarDaysIcon className="w-5 h-5 text-primary-600" />
                    업무 내역
                  </div>
                </CardTitle>
              </CardHeader>

              <div className="px-6 pb-6">
                {selectedDateTasks.length === 0 ? (
                  <div className="text-center py-8">
                    <CalendarDaysIcon className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">
                      {selectedDate ? '해당 날짜에 업무가 없습니다' : '날짜를 선택하세요'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin">
                    {selectedDateTasks.map((task, index) => (
                      <motion.div
                        key={task.task_id || index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <Badge variant="primary">{task.platform}</Badge>
                          <span className="text-xs text-gray-500">
                            {task.timestamp
                              ? format(new Date(task.timestamp), 'HH:mm')
                              : ''}
                          </span>
                        </div>
                        <p className="text-sm text-gray-900 mb-2">{task.content}</p>
                        <p className="text-xs text-gray-500">
                          {task.sender} → {task.receiver || '-'}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
