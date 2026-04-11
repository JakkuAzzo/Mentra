import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/store';

export default function Navigation() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-8">
          <Link to="/dashboard" className="text-2xl font-bold text-blue-600">
            Mentra
          </Link>
          <div className="flex gap-4">
            <Link
              to="/dashboard"
              className="text-gray-600 hover:text-gray-900 font-medium transition"
            >
              Dashboard
            </Link>
            <Link
              to="/progress"
              className="text-gray-600 hover:text-gray-900 font-medium transition"
            >
              Progress
            </Link>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {user?.full_name || user?.username}
          </span>
          <button
            onClick={handleLogout}
            className="btn btn-secondary"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
