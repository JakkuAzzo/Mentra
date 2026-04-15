import { useEffect, useMemo, useState } from 'react';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/store';

interface Community {
  id: number;
  name: string;
  description?: string;
  category: string;
  community_type: string;
  organization_name?: string;
  is_linked: boolean;
  member_count: number;
}

interface CommunityCourse {
  id: number;
  title: string;
  description?: string;
  topic_id?: number;
  topic_name?: string;
  milestone_points: number;
}

interface LeaderboardRow {
  rank: number;
  user_id: number;
  username: string;
  display_name: string;
  questions_attempted: number;
  average_accuracy: number;
  courses_completed: number;
  trophies: number;
  score: number;
  tier?: string;
  current_streak?: number;
}

interface Game {
  id: number;
  title: string;
  game_type: string;
  description?: string;
}

interface Trophy {
  id: number;
  user_id: number;
  username: string;
  title: string;
  description?: string;
  milestone_type: string;
  awarded_at: string;
}

interface Tournament {
  id: number;
  title: string;
  status: string;
  start_date: string;
  end_date: string;
  prize_pool?: string;
}

interface Streak {
  user_id: number;
  current_streak: number;
  longest_streak: number;
}

const getTierBadge = (tier?: string) => {
  const tierColors: Record<string, string> = {
    platinum: 'bg-cyan-100 text-cyan-800 border-cyan-300',
    gold: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    silver: 'bg-gray-200 text-gray-800 border-gray-400',
    bronze: 'bg-amber-100 text-amber-800 border-amber-300',
  };
  return tierColors[tier || 'bronze'] || tierColors.bronze;
};

export default function CommunitiesPage() {
  const user = useAuthStore((state) => state.user);

  const [joinedCommunities, setJoinedCommunities] = useState<Community[]>([]);
  const [discoverCommunities, setDiscoverCommunities] = useState<Community[]>([]);
  const [onboardingSuggestions, setOnboardingSuggestions] = useState<Community[]>([]);
  const [isFirstRun, setIsFirstRun] = useState(false);
  const [selectedCommunityId, setSelectedCommunityId] = useState<number | null>(null);

  const [courses, setCourses] = useState<CommunityCourse[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [recentTrophies, setRecentTrophies] = useState<Trophy[]>([]);
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [topStreaks, setTopStreaks] = useState<Streak[]>([]);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newCommunity, setNewCommunity] = useState({
    name: '',
    description: '',
    category: 'group',
    community_type: 'study',
    organization_name: '',
    is_linked: false,
  });

  const [newCourse, setNewCourse] = useState({
    title: '',
    description: '',
    topic_id: '',
    milestone_points: '100',
  });

  const [newTrophy, setNewTrophy] = useState({
    user_id: '',
    title: '',
    description: '',
    milestone_type: 'achievement',
  });

  const selectedCommunity = useMemo(
    () => joinedCommunities.find((community) => community.id === selectedCommunityId) || null,
    [joinedCommunities, selectedCommunityId]
  );

  const isPrivilegedCreator =
    user?.role === 'teacher' || user?.role === 'admin' || user?.role === 'manager' || user?.role === 'analyst';

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    fetchCommunities();
  }, [user?.id]);

  useEffect(() => {
    if (!selectedCommunityId) {
      setCourses([]);
      setLeaderboard([]);
      setGames([]);
      setRecentTrophies([]);
      setTournaments([]);
      setTopStreaks([]);
      return;
    }

    fetchCommunityDetails(selectedCommunityId);
  }, [selectedCommunityId]);

  const fetchCommunities = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get('/communities', {
        params: { user_id: user.id },
      });

      const joined = response.data.joined || [];
      const discover = response.data.discover || [];
      const suggestions = response.data.onboarding_suggestions || [];

      setJoinedCommunities(joined);
      setDiscoverCommunities(discover);
      setOnboardingSuggestions(suggestions);
      setIsFirstRun(Boolean(response.data.first_run));

      if (joined.length > 0) {
        setSelectedCommunityId((current) => current || joined[0].id);
      }
    } catch (fetchError) {
      console.error('Failed to load communities', fetchError);
      setError('Unable to load communities right now.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCommunityDetails = async (communityId: number) => {
    try {
      const [coursesRes, leaderboardRes, hubRes, tournamentsRes, streaksRes] = await Promise.all([
        apiClient.get(`/communities/${communityId}/courses`),
        apiClient.get(`/communities/${communityId}/leaderboard`),
        apiClient.get(`/communities/${communityId}/engagement-hub`),
        apiClient.get(`/communities/${communityId}/tournaments`).catch(() => ({ data: { tournaments: [] } })),
        apiClient.get(`/communities/${communityId}/streaks`).catch(() => ({ data: { top_streaks: [] } })),
      ]);

      setCourses(coursesRes.data || []);
      setLeaderboard(leaderboardRes.data.leaderboard || []);
      setGames(hubRes.data.games || []);
      setRecentTrophies(hubRes.data.recent_trophies || []);
      setTournaments(tournamentsRes.data.tournaments || []);
      setTopStreaks(streaksRes.data.top_streaks || []);
    } catch (fetchError) {
      console.error('Failed to load community details', fetchError);
      setError('Unable to load selected community details.');
    }
  };

  const handleCreateCommunity = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!user?.id) return;

    try {
      setBusy(true);
      setError(null);

      await apiClient.post('/communities', {
        user_id: user.id,
        ...newCommunity,
        organization_name: newCommunity.organization_name || null,
      });

      setNewCommunity({
        name: '',
        description: '',
        category: 'group',
        community_type: 'study',
        organization_name: '',
        is_linked: false,
      });
      await fetchCommunities();
    } catch (createError: any) {
      setError(createError.response?.data?.detail || 'Could not create community.');
    } finally {
      setBusy(false);
    }
  };

  const handleJoinCommunity = async (communityId: number) => {
    if (!user?.id) return;

    try {
      setBusy(true);
      setError(null);

      await apiClient.post(`/communities/${communityId}/join`, null, {
        params: { user_id: user.id },
      });

      await fetchCommunities();
      setSelectedCommunityId(communityId);
    } catch (joinError: any) {
      setError(joinError.response?.data?.detail || 'Could not join community.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateCourse = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!user?.id || !selectedCommunityId) return;

    try {
      setBusy(true);
      setError(null);

      await apiClient.post(`/communities/${selectedCommunityId}/courses`, {
        user_id: user.id,
        title: newCourse.title,
        description: newCourse.description || null,
        topic_id: newCourse.topic_id ? Number(newCourse.topic_id) : null,
        milestone_points: Number(newCourse.milestone_points || '100'),
      });

      setNewCourse({ title: '', description: '', topic_id: '', milestone_points: '100' });
      await fetchCommunityDetails(selectedCommunityId);
    } catch (courseError: any) {
      setError(courseError.response?.data?.detail || 'Could not create course.');
    } finally {
      setBusy(false);
    }
  };

  const handleAwardTrophy = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!user?.id || !selectedCommunityId) return;

    try {
      setBusy(true);
      setError(null);

      await apiClient.post(`/communities/${selectedCommunityId}/trophies`, {
        awarded_by_user_id: user.id,
        user_id: Number(newTrophy.user_id),
        title: newTrophy.title,
        description: newTrophy.description || null,
        milestone_type: newTrophy.milestone_type,
      });

      setNewTrophy({ user_id: '', title: '', description: '', milestone_type: 'achievement' });
      await fetchCommunityDetails(selectedCommunityId);
    } catch (trophyError: any) {
      setError(trophyError.response?.data?.detail || 'Could not award trophy.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateTournament = async () => {
    if (!selectedCommunityId) return;

    try {
      setBusy(true);
      setError(null);

      await apiClient.post(`/communities/${selectedCommunityId}/tournaments`, {
        title: `Weekly Challenge - ${new Date().toLocaleDateString()}`,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      });

      await fetchCommunityDetails(selectedCommunityId);
    } catch (tournamentError: any) {
      setError(tournamentError.response?.data?.detail || 'Could not create tournament.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading communities...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 space-y-8">
        <div>
          <h1 className="section-title">Communities</h1>
          <p className="text-gray-600">
            Join your university, workplace, or personal learning groups. Compete in tournaments, earn badges, and build daily streaks!
          </p>
        </div>

        {error && (
          <div className="card bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="card lg:col-span-1">
            <h2 className="subsection-title">Create Community</h2>
            {!isPrivilegedCreator && (
              <p className="text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded p-3 mb-4">
                ℹ️ Schools/Universities/Colleges require teacher/admin/manager role to create
              </p>
            )}
            <form onSubmit={handleCreateCommunity} className="space-y-4">
              <input
                type="text"
                placeholder="Community name"
                value={newCommunity.name}
                onChange={(e) => setNewCommunity({ ...newCommunity, name: e.target.value })}
                required
                className="input-field"
              />
              <textarea
                placeholder="Description"
                value={newCommunity.description}
                onChange={(e) => setNewCommunity({ ...newCommunity, description: e.target.value })}
                rows={3}
                className="input-field"
              />
              <select
                value={newCommunity.category}
                onChange={(e) => setNewCommunity({ ...newCommunity, category: e.target.value })}
                className="input-field"
              >
                <option value="group">Group</option>
                <option value="school">School</option>
                <option value="university">University</option>
                <option value="college">College</option>
                <option value="workplace">Workplace</option>
              </select>
              <select
                value={newCommunity.community_type}
                onChange={(e) => setNewCommunity({ ...newCommunity, community_type: e.target.value })}
                className="input-field"
              >
                <option value="study">Study Group</option>
                <option value="workplace">Workplace</option>
                <option value="bootcamp">Bootcamp</option>
                <option value="hobby">Hobby</option>
              </select>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={newCommunity.is_linked}
                  onChange={(e) => setNewCommunity({ ...newCommunity, is_linked: e.target.checked })}
                  className="w-4 h-4"
                />
                <span>Linked institutional community</span>
              </label>
              {newCommunity.is_linked && (
                <input
                  type="text"
                  placeholder="Organization name (optional)"
                  value={newCommunity.organization_name}
                  onChange={(e) => setNewCommunity({ ...newCommunity, organization_name: e.target.value })}
                  className="input-field"
                />
              )}
              <button type="submit" disabled={busy} className="btn btn-primary w-full">
                {busy ? '🔄 Creating...' : '✨ Create Community'}
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 space-y-6">
            {isFirstRun && onboardingSuggestions.length > 0 && (
              <div className="card bg-blue-50 border-l-4 border-blue-400">
                <h3 className="subsection-title text-blue-800">Onboarding: join your first community</h3>
                <p className="text-blue-700 text-sm mb-4">
                  Start with one of these recommended communities to unlock leaderboard, streaks, and peer learning.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {onboardingSuggestions.map((community) => (
                    <div key={community.id} className="bg-white border border-blue-200 rounded p-3">
                      <div className="font-semibold text-gray-800">{community.name}</div>
                      <p className="text-xs text-gray-600 mt-1">{community.description || 'Guided beginner community'}</p>
                      <button
                        onClick={() => handleJoinCommunity(community.id)}
                        disabled={busy}
                        className="btn btn-primary text-sm w-full mt-3"
                      >
                        One-click join
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="card">
              <h3 className="subsection-title">Your Communities</h3>
              {joinedCommunities.length === 0 ? (
                <p className="text-gray-500 text-sm">Join or create a community to get started</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {joinedCommunities.map((community) => (
                    <div
                      key={community.id}
                      onClick={() => setSelectedCommunityId(community.id)}
                      className={`cursor-pointer border-2 rounded-lg p-4 transition-all ${
                        selectedCommunityId === community.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-semibold text-gray-800">{community.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{community.category}</div>
                      <div className="text-xs text-blue-600 mt-2">👥 {community.member_count} members</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {discoverCommunities.length > 0 && (
              <div className="card">
                <h3 className="subsection-title">Discover Communities</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {discoverCommunities.slice(0, 6).map((community) => (
                    <div key={community.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="font-semibold text-gray-800 mb-2">{community.name}</div>
                      <p className="text-sm text-gray-600 mb-3">{community.description}</p>
                      <button
                        onClick={() => handleJoinCommunity(community.id)}
                        disabled={busy}
                        className="btn btn-secondary text-sm w-full"
                      >
                        Join Community
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {selectedCommunity && (
          <div className="space-y-6">
            <div>
              <h2 className="subsection-title">{selectedCommunity.name}</h2>
              <p className="text-gray-600">{selectedCommunity.description}</p>
            </div>

            {/* Leaderboard with Tiers & Streaks */}
            <div className="card">
              <h3 className="subsection-title">📊 Leaderboard</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      <th className="text-left px-4 py-2">Rank</th>
                      <th className="text-left px-4 py-2">Player</th>
                      <th className="text-center px-4 py-2">Tier</th>
                      <th className="text-right px-4 py-2">Score</th>
                      <th className="text-right px-4 py-2">Accuracy</th>
                      <th className="text-right px-4 py-2">Streak 🔥</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((row, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 font-semibold">{row.rank}</td>
                        <td className="px-4 py-3">{row.display_name}</td>
                        <td className="px-4 py-3 text-center">
                          {row.tier && (
                            <span className={`px-2 py-1 rounded border ${getTierBadge(row.tier)} text-xs font-semibold`}>
                              {row.tier.toUpperCase()}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold">{row.score}</td>
                        <td className="px-4 py-3 text-right">{row.average_accuracy}%</td>
                        <td className="px-4 py-3 text-right">{row.current_streak || 0} days</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Top Streaks */}
            {topStreaks.length > 0 && (
              <div className="card">
                <h3 className="subsection-title">🔥 Top Streaks</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {topStreaks.slice(0, 10).map((streak, idx) => (
                    <div
                      key={idx}
                      className={`border-2 rounded-lg p-4 text-center ${
                        idx === 0
                          ? 'border-yellow-400 bg-yellow-50'
                          : idx === 1
                            ? 'border-gray-400 bg-gray-50'
                            : 'border-amber-300 bg-amber-50'
                      }`}
                    >
                      <div className="text-2xl font-bold text-gray-800">#{idx + 1}</div>
                      <div className="text-lg font-semibold mt-2">{streak.current_streak} days 🔥</div>
                      <div className="text-xs text-gray-600 mt-1">Best: {streak.longest_streak} days</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tournaments Section */}
            {tournaments.length > 0 && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="subsection-title">🏆 Tournaments</h3>
                  {isPrivilegedCreator && (
                    <button
                      onClick={handleCreateTournament}
                      disabled={busy}
                      className="btn btn-secondary text-sm"
                    >
                      Start Tournament
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {tournaments.map((tournament) => (
                    <div key={tournament.id} className="border border-amber-200 bg-amber-50 rounded-lg p-4">
                      <div className="font-semibold text-amber-900">{tournament.title}</div>
                      <div className="text-sm text-amber-700 mt-2">Status: {tournament.status}</div>
                      <div className="text-xs text-amber-600 mt-1">🎁 {tournament.prize_pool}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Games & Challenges */}
            {games.length > 0 && (
              <div className="card">
                <h3 className="subsection-title">🎮 Games & Challenges</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {games.map((game) => (
                    <div key={game.id} className="border border-purple-200 bg-purple-50 rounded-lg p-4">
                      <div className="font-semibold text-purple-900">{game.title}</div>
                      <div className="text-sm text-purple-700 mt-2">{game.game_type.replace(/_/g, ' ')}</div>
                      {game.description && <p className="text-sm text-purple-600 mt-2">{game.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Trophies */}
            {recentTrophies.length > 0 && (
              <div className="card">
                <h3 className="subsection-title">🏅 Recent Achievements</h3>
                <div className="space-y-3">
                  {recentTrophies.slice(0, 5).map((trophy) => (
                    <div key={trophy.id} className="border-l-4 border-green-400 bg-green-50 p-3 rounded">
                      <div className="font-semibold text-green-900">{trophy.title}</div>
                      <div className="text-sm text-green-700 mt-1">{trophy.description}</div>
                      <div className="text-xs text-green-600 mt-1">Awarded to {trophy.username}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Community Courses */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="subsection-title">📚 Courses</h3>
                {isPrivilegedCreator && (
                  <button
                    onClick={() => {
                      const form = document.getElementById('courseForm') as HTMLFormElement;
                      if (form) form.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="text-blue-600 text-sm hover:underline"
                  >
                    Add Course
                  </button>
                )}
              </div>
              {courses.length === 0 ? (
                <p className="text-gray-500 text-sm">No courses yet</p>
              ) : (
                <div className="space-y-3">
                  {courses.map((course) => (
                    <div key={course.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="font-semibold text-gray-800">{course.title}</div>
                      {course.description && <p className="text-sm text-gray-600 mt-2">{course.description}</p>}
                      <div className="text-xs text-blue-600 mt-2">⭐ {course.milestone_points} points</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Add Course Form */}
            {isPrivilegedCreator && (
              <div className="card" id="courseForm">
                <h3 className="subsection-title">Add Course</h3>
                <form onSubmit={handleCreateCourse} className="space-y-4">
                  <input
                    type="text"
                    placeholder="Course title"
                    value={newCourse.title}
                    onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
                    required
                    className="input-field"
                  />
                  <textarea
                    placeholder="Course description"
                    value={newCourse.description}
                    onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                    rows={3}
                    className="input-field"
                  />
                  <input
                    type="number"
                    placeholder="Milestone points"
                    value={newCourse.milestone_points}
                    onChange={(e) => setNewCourse({ ...newCourse, milestone_points: e.target.value })}
                    className="input-field"
                  />
                  <button type="submit" disabled={busy} className="btn btn-primary w-full">
                    {busy ? '🔄 Adding...' : '➕ Add Course'}
                  </button>
                </form>
              </div>
            )}

            {/* Award Trophy Section */}
            {isPrivilegedCreator && (
              <div className="card">
                <h3 className="subsection-title">Award Trophy</h3>
                <form onSubmit={handleAwardTrophy} className="space-y-4">
                  <select
                    value={newTrophy.user_id}
                    onChange={(e) => setNewTrophy({ ...newTrophy, user_id: e.target.value })}
                    required
                    className="input-field"
                  >
                    <option value="">Select student</option>
                    {leaderboard.map((row) => (
                      <option key={row.user_id} value={row.user_id}>
                        {row.display_name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder="Trophy title"
                    value={newTrophy.title}
                    onChange={(e) => setNewTrophy({ ...newTrophy, title: e.target.value })}
                    required
                    className="input-field"
                  />
                  <textarea
                    placeholder="Description (optional)"
                    value={newTrophy.description}
                    onChange={(e) => setNewTrophy({ ...newTrophy, description: e.target.value })}
                    rows={2}
                    className="input-field"
                  />
                  <select
                    value={newTrophy.milestone_type}
                    onChange={(e) => setNewTrophy({ ...newTrophy, milestone_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="achievement">Achievement</option>
                    <option value="course_completion">Course Completion</option>
                    <option value="streak">Streak</option>
                  </select>
                  <button type="submit" disabled={busy} className="btn btn-success w-full">
                    {busy ? '🔄 Awarding...' : '🏆 Award Trophy'}
                  </button>
                </form>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
