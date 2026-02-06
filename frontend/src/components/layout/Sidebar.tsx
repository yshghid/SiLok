import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  HomeIcon,
  CalendarDaysIcon,
  ClipboardDocumentListIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  CalendarDaysIcon as CalendarDaysIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  DocumentTextIcon as DocumentTextIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
} from '@heroicons/react/24/solid';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  iconActive: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const navigation: NavItem[] = [
  { name: '대시보드', href: '/dashboard', icon: HomeIcon, iconActive: HomeIconSolid },
  {
    name: '캘린더',
    href: '/calendar',
    icon: CalendarDaysIcon,
    iconActive: CalendarDaysIconSolid,
  },
  {
    name: '업무 목록',
    href: '/tasks',
    icon: ClipboardDocumentListIcon,
    iconActive: ClipboardDocumentListIconSolid,
  },
  {
    name: '보고서',
    href: '/reports',
    icon: DocumentTextIcon,
    iconActive: DocumentTextIconSolid,
  },
  {
    name: '설정',
    href: '/settings',
    icon: Cog6ToothIcon,
    iconActive: Cog6ToothIconSolid,
  },
];

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg shadow-primary-500/30">
          <DocumentTextIcon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900">Weekly Report</h1>
          <p className="text-xs text-gray-500">AI 기반 보고서 생성</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-4 py-6 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  <item.iconActive className="w-5 h-5" />
                ) : (
                  <item.icon className="w-5 h-5" />
                )}
                {item.name}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
        <div className="px-4 py-3 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg">
          <p className="text-xs font-medium text-primary-700">AI 보고서 생성기</p>
          <p className="text-xs text-gray-500 mt-1">
            업무 데이터를 자동으로 분석합니다
          </p>
        </div>
      </div>
    </aside>
  );
}
