"use client";

import { useState, useEffect } from "react";
import { Bell, User, Settings, LogOut, RefreshCw } from "lucide-react";

interface SystemStats {
	total_scans?: number;
	status_counts?: Record<string, number>;
	recent_scans_7d?: number;
}

export function Header() {
	const [stats, setStats] = useState<SystemStats>({});
	const [isLoading, setIsLoading] = useState(false);
	const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

	const fetchStats = async () => {
		setIsLoading(true);
		try {
			const response = await fetch("/api/stats");
			if (response.ok) {
				const data = await response.json();
				setStats(data.statistics || {});
				setLastUpdate(new Date());
			}
		} catch (error) {
			console.error("Failed to fetch stats:", error);
		} finally {
			setIsLoading(false);
		}
	};

	useEffect(() => {
		fetchStats();
		// Refresh stats every 30 seconds
		const interval = setInterval(fetchStats, 30000);
		return () => clearInterval(interval);
	}, []);

	return (
		<header className="bg-white shadow-sm border-b border-gray-200">
			<div className="px-6 py-4">
				<div className="flex items-center justify-between">
					{/* Page Title & Stats */}
					<div className="flex items-center space-x-6">
						<div>
							<h2 className="text-2xl font-bold text-gray-900">
								Security Dashboard
							</h2>
							<p className="text-sm text-gray-600">
								Last updated: {lastUpdate.toLocaleTimeString()}
							</p>
						</div>

						{/* Quick Stats */}
						<div className="flex items-center space-x-4">
							<div className="bg-gray-50 rounded-lg px-4 py-2">
								<div className="text-sm font-medium text-gray-600">
									Total Scans
								</div>
								<div className="text-xl font-bold text-gray-900">
									{stats.total_scans || 0}
								</div>
							</div>
							<div className="bg-blue-50 rounded-lg px-4 py-2">
								<div className="text-sm font-medium text-blue-600">
									Recent (7d)
								</div>
								<div className="text-xl font-bold text-blue-900">
									{stats.recent_scans_7d || 0}
								</div>
							</div>
						</div>
					</div>

					{/* Right side actions */}
					<div className="flex items-center space-x-4">
						{/* Refresh Button */}
						<button
							onClick={fetchStats}
							disabled={isLoading}
							className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
							title="Refresh data"
						>
							<RefreshCw
								className={`h-5 w-5 ${isLoading ? "animate-spin" : ""}`}
							/>
						</button>

						{/* Notifications */}
						<div className="relative">
							<button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
								<Bell className="h-5 w-5" />
								{/* Notification badge */}
								<span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
									3
								</span>
							</button>
						</div>

						{/* Settings */}
						<button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
							<Settings className="h-5 w-5" />
						</button>

						{/* User Menu */}
						<div className="relative">
							<button className="flex items-center space-x-3 p-2 hover:bg-gray-100 rounded-lg transition-colors">
								<div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600">
									<User className="h-5 w-5 text-white" />
								</div>
								<div className="text-left">
									<div className="text-sm font-medium text-gray-900">
										Security Admin
									</div>
									<div className="text-xs text-gray-500">Administrator</div>
								</div>
							</button>
						</div>

						{/* System Status Indicator */}
						<div className="flex items-center space-x-2">
							<div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
							<span className="text-sm text-gray-600">Online</span>
						</div>
					</div>
				</div>
			</div>
		</header>
	);
}
