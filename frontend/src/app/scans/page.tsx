"use client";

import { useState, useEffect } from "react";
import {
	Activity,
	AlertTriangle,
	CheckCircle,
	XCircle,
	Clock,
	Eye,
	GitBranch,
	Calendar,
	Filter,
	Search,
	Download,
	RefreshCw,
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
	created_at: string;
	updated_at: string;
}

interface ScansResponse {
	scans: Scan[];
	count: number;
	filtered_by_repo?: string;
	timestamp: string;
}

export default function ScansPage() {
	const [scans, setScans] = useState<Scan[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [searchTerm, setSearchTerm] = useState("");
	const [statusFilter, setStatusFilter] = useState("all");
	const [limit, setLimit] = useState(50);

	const fetchScans = async () => {
		try {
			setIsLoading(true);
			setError(null);

			const response = await fetch(`/api/scans?limit=${limit}`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data: ScansResponse = await response.json();
			setScans(data.scans || []);
		} catch (error) {
			console.error("Failed to fetch scans:", error);
			setError(
				error instanceof Error ? error.message : "Failed to fetch scans",
			);
		} finally {
			setIsLoading(false);
		}
	};

	useEffect(() => {
		fetchScans();
	}, [limit]);

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleString("en-US", {
			month: "short",
			day: "numeric",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const formatDuration = (seconds: number) => {
		if (seconds < 60) {
			return `${seconds.toFixed(1)}s`;
		}
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
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

	const getStatusBadge = (status: string) => {
		switch (status) {
			case "completed":
				return "bg-green-100 text-green-800 border-green-200";
			case "failed":
				return "bg-red-100 text-red-800 border-red-200";
			case "running":
				return "bg-blue-100 text-blue-800 border-blue-200";
			default:
				return "bg-gray-100 text-gray-800 border-gray-200";
		}
	};

	const filteredScans = scans.filter((scan) => {
		const matchesSearch =
			scan.repo_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
			scan.branch.toLowerCase().includes(searchTerm.toLowerCase()) ||
			scan.commit_sha.toLowerCase().includes(searchTerm.toLowerCase());

		const matchesStatus =
			statusFilter === "all" || scan.scan_status === statusFilter;

		return matchesSearch && matchesStatus;
	});

	if (isLoading) {
		return (
			<div className="space-y-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">Recent Scans</h1>
						<p className="text-gray-600">Complete scan history and results</p>
					</div>
				</div>

				{/* Loading skeleton */}
				<div className="bg-white rounded-lg shadow-sm">
					<div className="animate-pulse">
						<div className="h-16 bg-gray-200 rounded-t-lg"></div>
						<div className="p-6 space-y-4">
							{[...Array(5)].map((_, i) => (
								<div key={i} className="h-16 bg-gray-200 rounded"></div>
							))}
						</div>
					</div>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="space-y-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">Recent Scans</h1>
						<p className="text-gray-600">Complete scan history and results</p>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm p-8 text-center">
					<XCircle className="mx-auto h-12 w-12 text-red-500" />
					<h3 className="mt-4 text-lg font-medium text-gray-900">
						Failed to load scans
					</h3>
					<p className="mt-2 text-sm text-gray-500">{error}</p>
					<button
						onClick={fetchScans}
						className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
					>
						<RefreshCw className="h-4 w-4 mr-2" />
						Try Again
					</button>
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold text-gray-900">Recent Scans</h1>
					<p className="text-gray-600">
						Complete scan history and results ({scans.length} total scans)
					</p>
				</div>
				<div className="flex items-center space-x-3">
					<button
						onClick={fetchScans}
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

			{/* Filters */}
			<div className="bg-white rounded-lg shadow-sm p-6">
				<div className="flex flex-col sm:flex-row gap-4">
					{/* Search */}
					<div className="flex-1">
						<div className="relative">
							<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
							<input
								type="text"
								placeholder="Search repositories, branches, or commit SHAs..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
							/>
						</div>
					</div>

					{/* Status Filter */}
					<div className="sm:w-48">
						<select
							value={statusFilter}
							onChange={(e) => setStatusFilter(e.target.value)}
							className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
						>
							<option value="all">All Statuses</option>
							<option value="completed">Completed</option>
							<option value="failed">Failed</option>
							<option value="running">Running</option>
						</select>
					</div>

					{/* Limit */}
					<div className="sm:w-24">
						<select
							value={limit}
							onChange={(e) => setLimit(Number(e.target.value))}
							className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
						>
							<option value="25">25</option>
							<option value="50">50</option>
							<option value="100">100</option>
							<option value="200">200</option>
						</select>
					</div>
				</div>
			</div>

			{/* Scans Table */}
			<div className="bg-white rounded-lg shadow-sm overflow-hidden">
				{filteredScans.length === 0 ? (
					<div className="px-6 py-12 text-center">
						<Activity className="mx-auto h-12 w-12 text-gray-400" />
						<h3 className="mt-2 text-sm font-medium text-gray-900">
							{searchTerm || statusFilter !== "all"
								? "No matching scans"
								: "No scans found"}
						</h3>
						<p className="mt-1 text-sm text-gray-500">
							{searchTerm || statusFilter !== "all"
								? "Try adjusting your search or filter criteria"
								: "Get started by running your first security scan"}
						</p>
						{!searchTerm && statusFilter === "all" && (
							<div className="mt-6">
								<a href="/scan" className="btn-primary">
									Start Scan
								</a>
							</div>
						)}
					</div>
				) : (
					<div className="overflow-x-auto">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-gray-50">
								<tr>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Repository
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Status
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Findings
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Duration
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Date
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Actions
									</th>
								</tr>
							</thead>
							<tbody className="bg-white divide-y divide-gray-200">
								{filteredScans.map((scan) => (
									<tr key={scan.id} className="hover:bg-gray-50">
										<td className="px-6 py-4 whitespace-nowrap">
											<div>
												<div className="text-sm font-medium text-gray-900">
													{scan.repo_name}
												</div>
												<div className="flex items-center mt-1 space-x-4">
													<div className="flex items-center text-xs text-gray-500">
														<GitBranch className="h-3 w-3 mr-1" />
														{scan.branch}
													</div>
													<div className="text-xs text-gray-500 font-mono">
														{scan.commit_sha.substring(0, 8)}
													</div>
												</div>
											</div>
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											<div className="flex items-center">
												{getStatusIcon(scan.scan_status)}
												<span
													className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBadge(scan.scan_status)}`}
												>
													{scan.scan_status}
												</span>
											</div>
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											<div className="flex items-center space-x-2">
												{scan.total_findings === 0 ? (
													<span className="text-sm text-gray-500">
														No issues
													</span>
												) : (
													<>
														{scan.critical_count > 0 && (
															<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
																{scan.critical_count} Critical
															</span>
														)}
														{scan.high_count > 0 && (
															<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
																{scan.high_count} High
															</span>
														)}
														{scan.medium_count > 0 && (
															<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
																{scan.medium_count} Medium
															</span>
														)}
														{scan.low_count > 0 && (
															<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
																{scan.low_count} Low
															</span>
														)}
													</>
												)}
											</div>
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
											{formatDuration(scan.scan_duration_seconds)}
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											<div className="flex items-center text-sm text-gray-500">
												<Calendar className="h-4 w-4 mr-1" />
												{formatDate(scan.scan_timestamp)}
											</div>
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
											<button className="text-primary-600 hover:text-primary-700 inline-flex items-center">
												<Eye className="h-4 w-4 mr-1" />
												View Details
											</button>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>

			{/* Footer Stats */}
			<div className="bg-white rounded-lg shadow-sm p-6">
				<div className="flex items-center justify-between text-sm text-gray-500">
					<div>
						Showing {filteredScans.length} of {scans.length} scans
						{searchTerm && ` matching "${searchTerm}"`}
						{statusFilter !== "all" && ` with status "${statusFilter}"`}
					</div>
					<div className="flex items-center space-x-4">
						<span>
							Total Findings:{" "}
							{scans.reduce((acc, scan) => acc + scan.total_findings, 0)}
						</span>
						<span>
							Avg Duration:{" "}
							{formatDuration(
								scans.reduce(
									(acc, scan) => acc + scan.scan_duration_seconds,
									0,
								) / scans.length,
							)}
						</span>
					</div>
				</div>
			</div>
		</div>
	);
}
