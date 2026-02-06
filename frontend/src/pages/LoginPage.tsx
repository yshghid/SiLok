import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { EnvelopeIcon, LockClosedIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { Button, Input } from '../components/common';
import { useAuthStore } from '../store';
import toast from 'react-hot-toast';

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState({
    email: '',
    password: '',
  });

  const validateForm = () => {
    const errors = { email: '', password: '' };
    let isValid = true;

    if (!formData.email) {
      errors.email = '이메일을 입력해주세요';
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = '올바른 이메일 형식이 아닙니다';
      isValid = false;
    }

    if (!formData.password) {
      errors.password = '비밀번호를 입력해주세요';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validateForm()) return;

    try {
      await login(formData);
      toast.success('로그인되었습니다');
      navigate('/dashboard');
    } catch {
      toast.error('로그인에 실패했습니다');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-3"
          >
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm">
              <DocumentTextIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Weekly Report</h1>
              <p className="text-primary-200 text-sm">AI 기반 보고서 생성기</p>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="relative z-10"
        >
          <h2 className="text-4xl font-bold text-white leading-tight mb-6">
            업무를 기록하고,
            <br />
            AI로 보고서를
            <br />
            자동 생성하세요
          </h2>
          <p className="text-primary-200 text-lg">
            Slack, Notion, OneDrive, Outlook의 업무 데이터를
            <br />
            분석하여 주간 보고서를 자동으로 생성합니다.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="relative z-10 flex items-center gap-6"
        >
          <div className="flex -space-x-2">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-10 h-10 rounded-full bg-white/20 border-2 border-white/30 backdrop-blur-sm flex items-center justify-center text-white text-sm font-medium"
              >
                {String.fromCharCode(65 + i)}
              </div>
            ))}
          </div>
          <p className="text-primary-200 text-sm">
            100+ 명의 사용자가 이용 중
          </p>
        </motion.div>
      </div>

      {/* Right side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg shadow-primary-500/30">
              <DocumentTextIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Weekly Report</h1>
              <p className="text-gray-500 text-sm">AI 기반 보고서 생성기</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-soft p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900">로그인</h2>
              <p className="text-gray-500 mt-2">계정에 로그인하여 시작하세요</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                name="email"
                type="email"
                label="이메일"
                placeholder="name@company.com"
                value={formData.email}
                onChange={handleChange}
                error={formErrors.email}
                leftIcon={<EnvelopeIcon className="w-5 h-5" />}
                autoComplete="email"
              />

              <Input
                name="password"
                type="password"
                label="비밀번호"
                placeholder="비밀번호를 입력하세요"
                value={formData.password}
                onChange={handleChange}
                error={formErrors.password}
                leftIcon={<LockClosedIcon className="w-5 h-5" />}
                autoComplete="current-password"
              />

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 bg-red-50 border border-red-200 rounded-lg"
                >
                  <p className="text-sm text-red-600">{error}</p>
                </motion.div>
              )}

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-600">로그인 유지</span>
                </label>
                <a
                  href="#"
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  비밀번호 찾기
                </a>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                isLoading={isLoading}
              >
                로그인
              </Button>
            </form>

            <div className="mt-8 text-center">
              <p className="text-sm text-gray-500">
                계정이 없으신가요?{' '}
                <a
                  href="#"
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  회원가입
                </a>
              </p>
            </div>
          </div>

          {/* Demo credentials hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100"
          >
            <p className="text-sm text-blue-800 font-medium mb-1">테스트 계정</p>
            <p className="text-sm text-blue-600">
              이메일: shyoun@skax.co.kr
              <br />
              비밀번호: 2222
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
