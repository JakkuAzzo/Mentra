import { useEffect, useMemo, useState } from 'react';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/store';

interface ProfileStats {
  total_questions_attempted: number;
  total_accuracy: number;
  topics_mastered: number;
  communities_joined: number;
  trophies_earned: number;
  courses_completed: number;
}

interface ProfileData {
  user_id: number;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  display_name?: string;
  avatar_style: string;
  profile_image_url?: string;
  bio?: string;
  institution?: string;
  workplace?: string;
  cv_headline?: string;
  cv_summary?: string;
  stats: ProfileStats;
}

interface CVData {
  full_name: string;
  display_name?: string;
  headline: string;
  summary: string;
  achievements: string[];
  course_completions: string[];
  milestone_trophies: Array<{
    title: string;
    milestone_type: string;
    awarded_at: string;
  }>;
}

export default function ProfilePage() {
  const authUser = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);

  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [cv, setCv] = useState<CVData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    display_name: '',
    avatar_style: 'scholar',
    profile_image_url: '',
    bio: '',
    institution: '',
    workplace: '',
    cv_headline: '',
    cv_summary: '',
  });

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
  });

  useEffect(() => {
    if (!authUser?.id) {
      setLoading(false);
      return;
    }

    fetchProfile();
  }, [authUser?.id]);

  const avatarEmoji = useMemo(() => {
    const map: Record<string, string> = {
      scholar: '🎓',
      explorer: '🧭',
      builder: '🛠️',
      strategist: '♟️',
      mentor: '🧠',
      creator: '🎨',
    };
    return map[form.avatar_style] || '🎓';
  }, [form.avatar_style]);

  const fetchProfile = async () => {
    if (!authUser?.id) return;

    try {
      setLoading(true);
      setError(null);

      const [profileRes, cvRes] = await Promise.all([
        apiClient.get(`/profile/${authUser.id}`),
        apiClient.get(`/profile/${authUser.id}/cv`),
      ]);

      const profileData: ProfileData = profileRes.data;
      const cvData: CVData = cvRes.data;

      setProfile(profileData);
      setCv(cvData);

      setForm({
        full_name: profileData.full_name || '',
        email: profileData.email || '',
        display_name: profileData.display_name || '',
        avatar_style: profileData.avatar_style || 'scholar',
        profile_image_url: profileData.profile_image_url || '',
        bio: profileData.bio || '',
        institution: profileData.institution || '',
        workplace: profileData.workplace || '',
        cv_headline: profileData.cv_headline || '',
        cv_summary: profileData.cv_summary || '',
      });
    } catch (fetchError) {
      console.error('Failed to load profile', fetchError);
      setError('Unable to load profile data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!authUser?.id) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await apiClient.put(`/profile/${authUser.id}`, {
        ...form,
        full_name: form.full_name || null,
        display_name: form.display_name || null,
        profile_image_url: form.profile_image_url || null,
        bio: form.bio || null,
        institution: form.institution || null,
        workplace: form.workplace || null,
        cv_headline: form.cv_headline || null,
        cv_summary: form.cv_summary || null,
      });

      const updatedProfile: ProfileData = response.data;
      setProfile(updatedProfile);

      if (authUser) {
        setUser({
          ...authUser,
          email: updatedProfile.email,
          full_name: updatedProfile.full_name || authUser.full_name,
        });
      }

      const cvRes = await apiClient.get(`/profile/${authUser.id}/cv`);
      setCv(cvRes.data);

      setSuccess('Profile updated successfully.');
    } catch (saveError: any) {
      setError(saveError.response?.data?.detail || 'Could not update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!authUser?.id) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      await apiClient.put(`/profile/${authUser.id}/password`, passwordForm);
      setPasswordForm({ current_password: '', new_password: '' });
      setSuccess('Password updated successfully.');
    } catch (passwordError: any) {
      setError(passwordError.response?.data?.detail || 'Could not update password.');
    } finally {
      setSaving(false);
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !authUser?.id) return;

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(`/profile/${authUser.id}/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const imageUrl = response.data.image_url;
      setForm((prev) => ({ ...prev, profile_image_url: imageUrl }));
      setSuccess('Profile image uploaded successfully! Click "Save Profile" to finalize.');
    } catch (uploadError: any) {
      setError(uploadError.response?.data?.detail || 'Could not upload image.');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Profile unavailable.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 space-y-8">
        <div>
          <h1 className="section-title">Profile</h1>
          <p className="text-gray-600">
            Personalize your identity, manage account settings, and maintain a professional learning CV.
          </p>
        </div>

        {error && (
          <div className="card bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {success && (
          <div className="card bg-green-50 border-l-4 border-green-400">
            <p className="text-green-700">{success}</p>
          </div>
        )}

        <div className="grid md:grid-cols-6 gap-4">
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Questions</p>
            <p className="text-2xl font-bold text-blue-700">{profile.stats.total_questions_attempted}</p>
          </div>
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Accuracy</p>
            <p className="text-2xl font-bold text-green-700">{profile.stats.total_accuracy.toFixed(1)}%</p>
          </div>
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Mastered</p>
            <p className="text-2xl font-bold text-purple-700">{profile.stats.topics_mastered}</p>
          </div>
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Communities</p>
            <p className="text-2xl font-bold text-indigo-700">{profile.stats.communities_joined}</p>
          </div>
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Trophies</p>
            <p className="text-2xl font-bold text-amber-700">{profile.stats.trophies_earned}</p>
          </div>
          <div className="card md:col-span-1">
            <p className="text-gray-500 text-xs uppercase">Courses Completed</p>
            <p className="text-2xl font-bold text-orange-700">{profile.stats.courses_completed}</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="card lg:col-span-2">
            <h2 className="subsection-title">Edit Profile</h2>
            <form className="space-y-3" onSubmit={handleSaveProfile}>
              <div className="grid md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  placeholder="Full name"
                  value={form.full_name}
                  onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
                />
                <input
                  type="email"
                  className="input-field"
                  placeholder="Email"
                  value={form.email}
                  onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                  required
                />
              </div>

              <div className="grid md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  placeholder="Display name"
                  value={form.display_name}
                  onChange={(event) => setForm((prev) => ({ ...prev, display_name: event.target.value }))}
                />
                <select
                  className="input-field"
                  value={form.avatar_style}
                  onChange={(event) => setForm((prev) => ({ ...prev, avatar_style: event.target.value }))}
                >
                  <option value="scholar">Scholar</option>
                  <option value="explorer">Explorer</option>
                  <option value="builder">Builder</option>
                  <option value="strategist">Strategist</option>
                  <option value="mentor">Mentor</option>
                  <option value="creator">Creator</option>
                </select>
              </div>

              <input
                className="input-field"
                placeholder="Profile image URL"
                value={form.profile_image_url}
                onChange={(event) => setForm((prev) => ({ ...prev, profile_image_url: event.target.value }))}
              />

              <div className="grid md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  placeholder="University / College"
                  value={form.institution}
                  onChange={(event) => setForm((prev) => ({ ...prev, institution: event.target.value }))}
                />
                <input
                  className="input-field"
                  placeholder="Workplace"
                  value={form.workplace}
                  onChange={(event) => setForm((prev) => ({ ...prev, workplace: event.target.value }))}
                />
              </div>

              <textarea
                className="input-field"
                placeholder="Bio"
                value={form.bio}
                onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))}
                rows={3}
              />

              <div className="grid md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  placeholder="CV headline"
                  value={form.cv_headline}
                  onChange={(event) => setForm((prev) => ({ ...prev, cv_headline: event.target.value }))}
                />
                <textarea
                  className="input-field"
                  placeholder="CV summary"
                  value={form.cv_summary}
                  onChange={(event) => setForm((prev) => ({ ...prev, cv_summary: event.target.value }))}
                  rows={2}
                />
              </div>

              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
            </form>
          </div>

          <div className="card">
            <h2 className="subsection-title">Avatar Preview</h2>
            <div className="flex flex-col items-center text-center">
              {form.profile_image_url ? (
                <img
                  src={form.profile_image_url}
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover border border-gray-200"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-4xl">
                  {avatarEmoji}
                </div>
              )}
              <p className="mt-3 font-semibold text-gray-900">{form.display_name || form.full_name || profile.username}</p>
              <p className="text-sm text-gray-500">{profile.role}</p>
            </div>

            <hr className="my-6" />

            <h3 className="font-semibold text-gray-800 mb-3">📸 Upload Profile Image</h3>
            <label className="block mb-4">
              <div className="border-2 border-dashed border-blue-300 rounded-lg p-4 text-center cursor-pointer hover:bg-blue-50 transition-all">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  disabled={uploading}
                  className="hidden"
                />
                <div className="text-blue-600 font-medium">
                  {uploading ? '🔄 Uploading...' : '📁 Choose Image or Drag & Drop'}
                </div>
                <p className="text-xs text-gray-600 mt-1">Max 5MB • JPEG, PNG, GIF, WebP</p>
              </div>
            </label>

            <hr className="my-6" />

            <h3 className="font-semibold text-gray-800 mb-3">Change Password</h3>
            <form className="space-y-3" onSubmit={handleUpdatePassword}>
              <input
                className="input-field"
                type="password"
                placeholder="Current password"
                value={passwordForm.current_password}
                onChange={(event) => setPasswordForm((prev) => ({ ...prev, current_password: event.target.value }))}
                required
              />
              <input
                className="input-field"
                type="password"
                placeholder="New password"
                value={passwordForm.new_password}
                onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))}
                minLength={8}
                required
              />
              <button className="btn btn-secondary w-full" type="submit" disabled={saving}>
                Update Password
              </button>
            </form>
          </div>
        </div>

        {cv && (
          <div className="card">
            <h2 className="subsection-title">My CV Builder</h2>
            <div className="border border-gray-200 rounded-lg p-6 bg-white">
              <h3 className="text-2xl font-bold text-gray-900">{cv.full_name}</h3>
              {cv.display_name && <p className="text-sm text-gray-500">Display name: {cv.display_name}</p>}
              <p className="text-lg text-blue-700 mt-2">{cv.headline}</p>
              <p className="text-gray-700 mt-4">{cv.summary}</p>

              <div className="grid md:grid-cols-2 gap-6 mt-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Key Achievements</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                    {cv.achievements.map((achievement) => (
                      <li key={achievement}>{achievement}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Course Completions</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                    {cv.course_completions.length > 0 ? (
                      cv.course_completions.map((completion) => <li key={completion}>{completion}</li>)
                    ) : (
                      <li>Keep learning to add validated course completions.</li>
                    )}
                  </ul>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="font-semibold text-gray-900 mb-2">Milestone Trophies</h4>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {cv.milestone_trophies.length > 0 ? (
                    cv.milestone_trophies.map((trophy) => (
                      <div key={`${trophy.title}-${trophy.awarded_at}`} className="p-3 rounded border border-yellow-200 bg-yellow-50">
                        <p className="font-medium text-yellow-900">🏆 {trophy.title}</p>
                        <p className="text-xs text-yellow-700">{trophy.milestone_type.replace('_', ' ')}</p>
                        <p className="text-xs text-yellow-700">{trophy.awarded_at}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No trophies yet.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
