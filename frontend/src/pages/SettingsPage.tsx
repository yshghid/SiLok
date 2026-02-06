import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UserCircleIcon,
  BellIcon,
  LinkIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { Header } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Badge } from '../components/common';
import { useAuthStore } from '../store';
import toast from 'react-hot-toast';
import { clsx } from 'clsx';

const tabs = [
  { id: 'profile', name: '프로필', icon: UserCircleIcon },
  { id: 'notifications', name: '알림', icon: BellIcon },
  { id: 'integrations', name: '연동', icon: LinkIcon },
  { id: 'security', name: '보안', icon: ShieldCheckIcon },
];

const integrations = [
  {
    id: 'slack',
    name: 'Slack',
    description: '슬랙 메시지 및 채널 데이터 연동',
    connected: true,
    icon: '💬',
  },
  {
    id: 'notion',
    name: 'Notion',
    description: '노션 페이지 및 데이터베이스 연동',
    connected: true,
    icon: '📝',
  },
  {
    id: 'onedrive',
    name: 'OneDrive',
    description: '원드라이브 파일 및 문서 연동',
    connected: true,
    icon: '☁️',
  },
  {
    id: 'outlook',
    name: 'Outlook',
    description: '아웃룩 이메일 및 일정 연동',
    connected: true,
    icon: '📧',
  },
];

export function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    department: '',
    position: '',
  });

  const handleSaveProfile = () => {
    toast.success('프로필이 저장되었습니다');
  };

  const handleToggleIntegration = (id: string) => {
    toast.success(`${id} 연동 상태가 변경되었습니다`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title="설정"
        subtitle="계정 및 앱 설정을 관리하세요"
      />

      <main className="p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col md:flex-row gap-8">
            {/* Sidebar */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="md:w-64 flex-shrink-0"
            >
              <Card padding="sm">
                <nav className="space-y-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={clsx(
                        'w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all',
                        activeTab === tab.id
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-50'
                      )}
                    >
                      <tab.icon className="w-5 h-5" />
                      {tab.name}
                    </button>
                  ))}
                </nav>
              </Card>
            </motion.div>

            {/* Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex-1"
            >
              {activeTab === 'profile' && (
                <Card>
                  <CardHeader>
                    <CardTitle subtitle="계정 정보를 수정하세요">프로필 설정</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Avatar */}
                      <div className="flex items-center gap-6">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-2xl font-bold">
                          {user?.name?.charAt(0) || 'U'}
                        </div>
                        <div>
                          <Button variant="secondary" size="sm">
                            이미지 변경
                          </Button>
                          <p className="text-xs text-gray-500 mt-2">
                            JPG, PNG 파일 (최대 2MB)
                          </p>
                        </div>
                      </div>

                      {/* Form */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input
                          label="이름"
                          value={formData.name}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                        />
                        <Input
                          label="이메일"
                          type="email"
                          value={formData.email}
                          onChange={(e) =>
                            setFormData({ ...formData, email: e.target.value })
                          }
                        />
                        <Input
                          label="부서"
                          placeholder="예: 개발팀"
                          value={formData.department}
                          onChange={(e) =>
                            setFormData({ ...formData, department: e.target.value })
                          }
                        />
                        <Input
                          label="직책"
                          placeholder="예: 시니어 개발자"
                          value={formData.position}
                          onChange={(e) =>
                            setFormData({ ...formData, position: e.target.value })
                          }
                        />
                      </div>

                      <div className="flex justify-end">
                        <Button onClick={handleSaveProfile}>저장하기</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {activeTab === 'notifications' && (
                <Card>
                  <CardHeader>
                    <CardTitle subtitle="알림 설정을 관리하세요">알림 설정</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {[
                        { id: 'email', label: '이메일 알림', description: '보고서 생성 완료 시 이메일로 알림' },
                        { id: 'push', label: '푸시 알림', description: '브라우저 푸시 알림 받기' },
                        { id: 'weekly', label: '주간 리마인더', description: '매주 금요일 보고서 생성 리마인더' },
                      ].map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-gray-900">{item.label}</p>
                            <p className="text-sm text-gray-500">{item.description}</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" defaultChecked />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                          </label>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {activeTab === 'integrations' && (
                <Card>
                  <CardHeader>
                    <CardTitle subtitle="외부 서비스 연동을 관리하세요">연동 관리</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {integrations.map((integration) => (
                        <div
                          key={integration.id}
                          className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <span className="text-2xl">{integration.icon}</span>
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-gray-900">{integration.name}</p>
                                {integration.connected && (
                                  <Badge variant="success">연동됨</Badge>
                                )}
                              </div>
                              <p className="text-sm text-gray-500">{integration.description}</p>
                            </div>
                          </div>
                          <Button
                            variant={integration.connected ? 'ghost' : 'primary'}
                            size="sm"
                            onClick={() => handleToggleIntegration(integration.id)}
                          >
                            {integration.connected ? '연동 해제' : '연동하기'}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {activeTab === 'security' && (
                <Card>
                  <CardHeader>
                    <CardTitle subtitle="계정 보안 설정을 관리하세요">보안 설정</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">비밀번호 변경</h4>
                        <p className="text-sm text-gray-500 mb-4">
                          보안을 위해 주기적으로 비밀번호를 변경하세요
                        </p>
                        <Button variant="secondary" size="sm">
                          비밀번호 변경
                        </Button>
                      </div>

                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">2단계 인증</h4>
                        <p className="text-sm text-gray-500 mb-4">
                          계정 보안을 강화하기 위해 2단계 인증을 활성화하세요
                        </p>
                        <Button variant="secondary" size="sm">
                          설정하기
                        </Button>
                      </div>

                      <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                        <h4 className="font-medium text-red-700 mb-2">계정 삭제</h4>
                        <p className="text-sm text-red-600 mb-4">
                          계정을 삭제하면 모든 데이터가 영구적으로 삭제됩니다
                        </p>
                        <Button variant="danger" size="sm">
                          계정 삭제
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}
