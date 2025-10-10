"use client";

import { useState, useEffect } from "react";
import {
	Database,
	Server,
	Activity,
	CheckCircle,
	XCircle,
	Clock,
	AlertTriangle,
	RefreshCw,
	Zap,
	HardDrive,
	Cpu,
	Globe,
	Shield,
} from "lucide-react";

interface HealthData {
	status: string;
	timestamp: string;
	database: string;
	total_scans: number;
}

interface ServiceInfo {
	service: string;
	version: string;
	status: string;
	endpoints: Record<string, string>;
	timestamp: string;
}

interface SystemStats {
	total_scans: number;
	status_counts: Record<string, number>;
	recent_scans_7d: number;
	total_findings: number;
	severity_counts: Record<string, number>;
}

export default function StatusPage() {
	const [health, setHealth] = useState<HealthData | null>(null);
	const [serviceInfo, setServiceInfo] = useState<ServiceInfo | null>(null);
	const [stats, setStats] = useState<SystemStats | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

	const fetchSystemStatus = async () => {
		try {
			setError(null);

			const [healthResponse, serviceResponse, statsResponse] =
				await Promise.all([
					fetch("/api/health").catch(() => null),
					fetch("/api/").catch(() => null),
					fetch("/api/stats").catch(() => null),
				]);

			// Health data
			if (healthResponse?.ok) {
				const healthData = await healthResponse.json();
				setHealth(healthData);
			}

			// Service info
			if (serviceResponse?.ok) {
				const serviceData = await serviceResponse.json();
				setServiceInfo(serviceData);
			}

			// System stats
			if (statsResponse?.ok) {
				const statsData = await statsResponse.json();
				setStats(statsData.statistics);
			}

			setLastUpdate(new Date());
		} catch (error) {
			console.error("Failed to fetch system status:", error);
			setError(
				error instanceof Error
					? error.message
					: "Failed to fetch system status",
			);
		} finally {
			setIsLoading(false);
		}
	};

	useEffect(() => {
		fetchSystemStatus();
		// Refresh every 30 seconds
		const interval = setInterval(fetchSystemStatus, 30000);
		return () => clearInterval(interval);
	}, []);

	const getStatusColor = (status: string) => {
		switch (status?.toLowerCase()) {
			case "healthy":
			case "running":
			case "connected":
				return "text-green-600 bg-green-50 border-green-200";
			case "warning":
			case "degraded":
				return "text-yellow-600 bg-yellow-50 border-yellow-200";
			case "error":
			case "failed":
			case "disconnected":
				return "text-red-600 bg-red-50 border-red-200";
			default:
				return "text-gray-600 bg-gray-50 border-gray-200";
		}
	};

	const getStatusIcon = (status: string) => {
		switch (status?.toLowerCase()) {
			case "healthy":
			case "running":
			case "connected":
				return <CheckCircle className="h-5 w-5 text-green-500" />;
			case "warning":
			case "degraded":
				return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
			case "error":
			case "failed":
			case "disconnected":
				return <XCircle className="h-5 w-5 text-red-500" />;
			default:
				return <Clock className="h-5 w-5 text-gray-500" />;
		}
	};

	const formatUptime = (timestamp: string) => {
		try {
			const startTime = new Date(timestamp);
			const now = new Date();
			const diffMs = now.getTime() - startTime.getTime();
			const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
			const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

			if (diffHours > 0) {
				return `${diffHours}h ${diffMinutes}m`;
			}
			return `${diffMinutes}m`;
		} catch {
			return "Unknown";
		}
	};

	if (isLoading) {
		return (
			<div className="space-y-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">System Status</h1>
						<p className="text-gray-600">Service health and monitoring</p>
					</div>
				</div>

				{/* Loading skeleton */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{[...Array(6)].map((_, i) => (
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

	const overallStatus =
		health?.status === "healthy" && serviceInfo?.status === "running"
			? "healthy"
			: "degraded";

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold text-gray-900">System Status</h1>
					<p className="text-gray-600">
						Service health and monitoring • Last updated:{" "}
						{lastUpdate.toLocaleTimeString()}
					</p>
				</div>
				<div className="flex items-center space-x-3">
					<div className="flex items-center space-x-2">
						{getStatusIcon(overallStatus)}
						<span
							className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(overallStatus)}`}
						>
							System {overallStatus === "healthy" ? "Healthy" : "Degraded"}
						</span>
					</div>
					<button
						onClick={fetchSystemStatus}
						disabled={isLoading}
						className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
					>
						<RefreshCw
							className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
						/>
						Refresh
					</button>
				</div>
			</div>

			{error && (
				<div className="bg-red-50 border border-red-200 rounded-lg p-4">
					<div className="flex">
						<XCircle className="h-5 w-5 text-red-400" />
						<div className="ml-3">
							<h3 className="text-sm font-medium text-red-800">
								Error fetching system status
							</h3>
							<p className="mt-1 text-sm text-red-700">{error}</p>
						</div>
					</div>
				</div>
			)}

			{/* Service Overview */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Shield className="h-8 w-8 text-primary-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Service</p>
							<p className="text-lg font-semibold text-gray-900">
								{serviceInfo?.service || "Watchman"}
							</p>
							<p className="text-xs text-gray-500">
								v{serviceInfo?.version || "1.0.0"}
							</p>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Server className="h-8 w-8 text-green-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Backend</p>
							<div className="flex items-center space-x-2">
								{getStatusIcon(serviceInfo?.status || "unknown")}
								<span className="text-lg font-semibold text-gray-900">
									{serviceInfo?.status || "Unknown"}
								</span>
							</div>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Database className="h-8 w-8 text-blue-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Database</p>
							<div className="flex items-center space-x-2">
								{getStatusIcon(health?.database || "unknown")}
								<span className="text-lg font-semibold text-gray-900">
									{health?.database || "Unknown"}
								</span>
							</div>
						</div>
					</div>
				</div>

				<div className="bg-white p-6 rounded-lg shadow-sm">
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Clock className="h-8 w-8 text-purple-600" />
						</div>
						<div className="ml-4">
							<p className="text-sm font-medium text-gray-600">Uptime</p>
							<p className="text-lg font-semibold text-gray-900">
								{health?.timestamp ? formatUptime(health.timestamp) : "Unknown"}
							</p>
						</div>
					</div>
				</div>
			</div>

			{/* System Metrics */}
			{stats && (
				<div className="bg-white rounded-lg shadow-sm">
					<div className="px-6 py-4 border-b border-gray-200">
						<h3 className="text-lg font-semibold text-gray-900">
							System Metrics
						</h3>
					</div>
					<div className="p-6">
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
							<div className="text-center">
								<div className="flex items-center justify-center">
									<Activity className="h-8 w-8 text-blue-600 mr-2" />
									<div>
										<p className="text-2xl font-bold text-gray-900">
											{stats.total_scans}
										</p>
										<p className="text-sm text-gray-600">Total Scans</p>
									</div>
								</div>
							</div>

							<div className="text-center">
								<div className="flex items-center justify-center">
									<CheckCircle className="h-8 w-8 text-green-600 mr-2" />
									<div>
										<p className="text-2xl font-bold text-gray-900">
											{stats.status_counts?.completed || 0}
										</p>
										<p className="text-sm text-gray-600">Completed</p>
									</div>
								</div>
							</div>

							<div className="text-center">
								<div className="flex items-center justify-center">
									<XCircle className="h-8 w-8 text-red-600 mr-2" />
									<div>
										<p className="text-2xl font-bold text-gray-900">
											{stats.status_counts?.failed || 0}
										</p>
										<p className="text-sm text-gray-600">Failed</p>
									</div>
								</div>
							</div>

							<div className="text-center">
								<div className="flex items-center justify-center">
									<AlertTriangle className="h-8 w-8 text-orange-600 mr-2" />
									<div>
										<p className="text-2xl font-bold text-gray-900">
											{stats.total_findings}
										</p>
										<p className="text-sm text-gray-600">Total Findings</p>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* API Endpoints */}
			{serviceInfo?.endpoints && (
				<div className="bg-white rounded-lg shadow-sm">
					<div className="px-6 py-4 border-b border-gray-200">
						<h3 className="text-lg font-semibold text-gray-900">
							API Endpoints
						</h3>
					</div>
					<div className="p-6">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							{Object.entries(serviceInfo.endpoints).map(([name, path]) => (
								<div
									key={name}
									className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
								>
									<div className="flex items-center space-x-3">
										<Globe className="h-4 w-4 text-gray-500" />
										<div>
											<p className="text-sm font-medium text-gray-900">
												{name
													.replace(/_/g, " ")
													.replace(/\b\w/g, (l) => l.toUpperCase())}
											</p>
											<p className="text-xs text-gray-500 font-mono">{path}</p>
										</div>
									</div>
									<div className="h-2 w-2 bg-green-500 rounded-full"></div>
								</div>
							))}
						</div>
					</div>
				</div>
			)}

			{/* Health Check Details */}
			{health && (
				<div className="bg-white rounded-lg shadow-sm">
					<div className="px-6 py-4 border-b border-gray-200">
						<h3 className="text-lg font-semibold text-gray-900">
							Health Check
						</h3>
					</div>
					<div className="p-6">
						<div className="space-y-4">
							<div className="flex items-center justify-between">
								<div className="flex items-center space-x-3">
									{getStatusIcon(health.status)}
									<div>
										<p className="text-sm font-medium text-gray-900">
											Overall Status
										</p>
										<p className="text-xs text-gray-500">
											Last checked:{" "}
											{new Date(health.timestamp).toLocaleString()}
										</p>
									</div>
								</div>
								<span
									className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(health.status)}`}
								>
									{health.status}
								</span>
							</div>

							<div className="flex items-center justify-between">
								<div className="flex items-center space-x-3">
									{getStatusIcon(health.database)}
									<div>
										<p className="text-sm font-medium text-gray-900">
											Database Connection
										</p>
										<p className="text-xs text-gray-500">
											{health.total_scans} scans in database
										</p>
									</div>
								</div>
								<span
									className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(health.database)}`}
								>
									{health.database}
								</span>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
