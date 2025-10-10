"use client";

import { useState, useEffect } from "react";
import {
	Shield,
	Activity,
	AlertTriangle,
	Clock,
	TrendingUp,
	CheckCircle,
	XCircle,
	Eye,
	ExternalLink,
	GitBranch,
	Calendar,
} from "lucide-react";

interface Scan {
	id: number;
	repo_name: string;
	branch: string;
	commit_sha: string;
	scan_status: string;
	total_findings: number;
	critical_count: number;
	high_count: number;
	medium_count: number;
	low_count: number;
	scan_timestamp: string;
	scan_duration_seconds: number;
}

interface SystemStats {
	total_scans: number;
	status_counts: Record<string, number>;
	recent_scans_7d: number;
	total_findings: number;
	severity_counts: Record<string, number>;
}

export default function Dashboard() {
	const [stats, setStats] = useState<SystemStats | null>(null);
	const [recentScans, setRecentScans] = useState<Scan[]>([]);
	const [isLoading, setIsLoading] = useState(true);

	const fetchData = async () => {
		try {
			const [statsResponse, scansResponse] = await Promise.all([
				fetch("/api/stats"),
				fetch("/api/scans?limit=5"),
			]);

			if (statsResponse.ok) {
				const statsData = await statsResponse.json();
				setStats(statsData.statistics);
			}

			if (scansResponse.ok) {
				const scansData = await scansResponse.json();
				setRecentScans(scansData.scans);
			}
		} catch (error) {
			console.error("Failed to fetch data:", error);
		} finally {
			setIsLoading(false);
		}
	};

	useEffect(() => {
		fetchData();
		// Refresh every 10 seconds
		const interval = setInterval(fetchData, 10000);
		return () => clearInterval(interval);
	}, []);

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString("en-US", {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const getSeverityColor = (severity: string) => {
		switch (severity.toLowerCase()) {
			case "error":
			case "critical":
				return "text-red-600 bg-red-50";
			case "warning":
			case "high":
				return "text-yellow-600 bg-yellow-50";
			case "medium":
				return "text-blue-600 bg-blue-50";
			case "low":
			case "info":
				return "text-gray-600 bg-gray-50";
			default:
				return "text-gray-600 bg-gray-50";
		}
	};

	const getStatusIcon = (status: string) => {
		switch (status) {
			case "completed":
				return <CheckCircle className="h-5 w-5 text-green-500" />;
			case "failed":
				return <XCircle className="h-5 w-5 text-red-500" />;
			case "running":
				return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
			default:
				return <Clock className="h-5 w-5 text-gray-500" />;
		}
	};

	if (isLoading) {
		return (
			<div className="space-y-6">
				{/* Loading skeleton */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
					{[...Array(4)].map((_, i) => (
						<div key={i} className="bg-white p-6 rounded-lg shadow-sm">
							<div className="animate-pulse">
								<div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
								<div className="h-8 bg-gray-200 rounded w-1/2"></div>
							</div>
						</div>
					))}
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
					<p className="text-gray-600">
						Overview of your security scanning activity
					</p>
				</div>
				<div className="flex items-center space-x-2">
					<div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
					<span className="text-sm text-gray-600">Real-time monitoring</span>
				</div>
			</div>

			{/* Stats Cards */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Activity className="h-8 w-8 text-blue-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Total Scans</p>
							<p className="text-2xl font-bold text-gray-900">
								{stats?.total_scans || 0}
							</p>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<AlertTriangle className="h-8 w-8 text-red-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">
								Critical Issues
							</p>
							<p className="text-2xl font-bold text-gray-900">
								{stats?.severity_counts?.ERROR || 0}
							</p>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<TrendingUp className="h-8 w-8 text-green-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Recent (7d)</p>
							<p className="text-2xl font-bold text-gray-900">
								{stats?.recent_scans_7d || 0}
							</p>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Shield className="h-8 w-8 text-purple-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">
								Total Findings
							</p>
							<p className="text-2xl font-bold text-gray-900">
								{stats?.total_findings || 0}
							</p>
						</div>
					</div>
				</div>
			</div>

			{/* Recent Scans */}
			<div className="bg-white rounded-lg shadow-sm">
				<div className="px-6 py-4 border-b border-gray-200">
					<div className="flex items-center justify-between">
						<h3 className="text-lg font-semibold text-gray-900">
							Recent Scans
						</h3>
						<a
							href="/scans"
							className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center"
						>
							View all <ExternalLink className="ml-1 h-4 w-4" />
						</a>
					</div>
				</div>

				<div className="divide-y divide-gray-200">
					{recentScans.length === 0 ? (
						<div className="px-6 py-8 text-center">
							<Activity className="mx-auto h-12 w-12 text-gray-400" />
							<h3 className="mt-2 text-sm font-medium text-gray-900">
								No scans yet
							</h3>
							<p className="mt-1 text-sm text-gray-500">
								Get started by running your first security scan
							</p>
							<div className="mt-6">
								<a href="/scan" className="btn-primary">
									Start Scan
								</a>
							</div>
						</div>
					) : (
						recentScans.map((scan) => (
							<div key={scan.id} className="px-6 py-4 hover:bg-gray-50">
								<div className="flex items-center justify-between">
									<div className="flex items-center space-x-4">
										{getStatusIcon(scan.scan_status)}
										<div>
											<h4 className="text-sm font-medium text-gray-900">
												{scan.repo_name}
											</h4>
											<div className="flex items-center space-x-4 mt-1">
												<div className="flex items-center text-xs text-gray-500">
													<GitBranch className="h-3 w-3 mr-1" />
													{scan.branch}
												</div>
												<div className="flex items-center text-xs text-gray-500">
													<Calendar className="h-3 w-3 mr-1" />
													{formatDate(scan.scan_timestamp)}
												</div>
												<span className="text-xs text-gray-500">
													{scan.scan_duration_seconds?.toFixed(1)}s
												</span>
											</div>
										</div>
									</div>

									<div className="flex items-center space-x-4">
										{/* Findings badges */}
										{scan.critical_count > 0 && (
											<span className="badge-critical">
												{scan.critical_count} Critical
											</span>
										)}
										{scan.high_count > 0 && (
											<span className="badge-high">{scan.high_count} High</span>
										)}
										{scan.medium_count > 0 && (
											<span className="badge-medium">
												{scan.medium_count} Medium
											</span>
										)}
										{scan.low_count > 0 && (
											<span className="badge-low">{scan.low_count} Low</span>
										)}

										<button className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center">
											<Eye className="h-4 w-4 mr-1" />
											View
										</button>
									</div>
								</div>
							</div>
						))
					)}
				</div>
			</div>

			{/* Quick Actions */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center space-x-3">
						<div className="flex-shrink-0">
							<Shield className="h-8 w-8 text-primary-600" />
						</div>
						<div className="flex-1">
							<h3 className="text-lg font-medium text-gray-900">
								Run Manual Scan
							</h3>
							<p className="text-sm text-gray-600 mt-1">
								Trigger a security scan on any repository
							</p>
							<a href="/scan" className="mt-3 btn-primary text-sm">
								Start Scan
							</a>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center space-x-3">
						<div className="flex-shrink-0">
							<Activity className="h-8 w-8 text-green-600" />
						</div>
						<div className="flex-1">
							<h3 className="text-lg font-medium text-gray-900">
								System Status
							</h3>
							<p className="text-sm text-gray-600 mt-1">
								Monitor system health and performance
							</p>
							<a href="/status" className="mt-3 btn-secondary text-sm">
								View Status
							</a>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center space-x-3">
						<div className="flex-shrink-0">
							<AlertTriangle className="h-8 w-8 text-yellow-600" />
						</div>
						<div className="flex-1">
							<h3 className="text-lg font-medium text-gray-900">
								Security Alerts
							</h3>
							<p className="text-sm text-gray-600 mt-1">
								View and manage security findings
							</p>
							<a href="/alerts" className="mt-3 btn-secondary text-sm">
								View Alerts
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
