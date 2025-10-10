"use client";

import { useState } from "react";
import {
	Search,
	GitBranch,
	Loader2,
	CheckCircle,
	XCircle,
	AlertTriangle,
	Clock,
	ExternalLink,
	RefreshCw,
} from "lucide-react";

interface ScanResult {
	success: boolean;
	scan_run_id?: number;
	message: string;
	workflow_id?: string;
	error?: string;
}

interface ScanProgress {
	status: "idle" | "scanning" | "completed" | "failed";
	message: string;
	details?: any;
}

export default function ManualScanPage() {
	const [repoName, setRepoName] = useState("");
	const [branch, setBranch] = useState("main");
	const [isScanning, setIsScanning] = useState(false);
	const [scanProgress, setScanProgress] = useState<ScanProgress>({
		status: "idle",
		message: "",
	});
	const [scanResult, setScanResult] = useState<ScanResult | null>(null);

	const startScan = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!repoName.trim()) {
			alert("Please enter a repository name");
			return;
		}

		setIsScanning(true);
		setScanResult(null);
		setScanProgress({ status: "scanning", message: "Initializing scan..." });

		try {
			const response = await fetch("/api/scan/manual", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					repo_name: repoName.trim(),
					branch: branch.trim(),
				}),
			});

			const result = await response.json();
			setScanResult(result);

			if (result.success) {
				setScanProgress({
					status: "scanning",
					message: "Scan started successfully! Processing in background...",
				});

				// Start polling for scan status if we have a scan_run_id
				if (result.scan_run_id) {
					pollScanStatus(result.scan_run_id);
				} else {
					// If no scan_run_id, just show completion after delay
					setTimeout(() => {
						setScanProgress({
							status: "completed",
							message: "Scan completed! Check recent scans for results.",
						});
						setIsScanning(false);
					}, 5000);
				}
			} else {
				setScanProgress({
					status: "failed",
					message: result.message || "Scan failed to start",
				});
				setIsScanning(false);
			}
		} catch (error) {
			console.error("Scan request failed:", error);
			setScanResult({
				success: false,
				message: "Failed to communicate with server",
				error: error instanceof Error ? error.message : "Unknown error",
			});
			setScanProgress({
				status: "failed",
				message: "Failed to start scan",
			});
			setIsScanning(false);
		}
	};

	const pollScanStatus = async (scanId: number) => {
		let attempts = 0;
		const maxAttempts = 60; // Poll for up to 5 minutes

		const poll = async () => {
			if (attempts >= maxAttempts) {
				setScanProgress({
					status: "completed",
					message: "Scan is taking longer than expected. Check recent scans.",
				});
				setIsScanning(false);
				return;
			}

			try {
				const response = await fetch(`/api/scan/${scanId}`);
				if (response.ok) {
					const data = await response.json();
					const scan = data.scan_run;

					if (scan) {
						if (scan.scan_status === "completed") {
							setScanProgress({
								status: "completed",
								message: `Scan completed! Found ${scan.total_findings || 0} security issues.`,
								details: scan,
							});
							setIsScanning(false);
							return;
						} else if (scan.scan_status === "failed") {
							setScanProgress({
								status: "failed",
								message: "Scan failed during processing",
								details: scan,
							});
							setIsScanning(false);
							return;
						} else if (scan.scan_status === "running") {
							setScanProgress({
								status: "scanning",
								message:
									"Scan is running... analyzing security vulnerabilities",
							});
						}
					}
				}

				attempts++;
				setTimeout(poll, 5000); // Poll every 5 seconds
			} catch (error) {
				console.error("Failed to poll scan status:", error);
				attempts++;
				setTimeout(poll, 5000);
			}
		};

		// Start polling after a short delay
		setTimeout(poll, 2000);
	};

	const resetForm = () => {
		setRepoName("");
		setBranch("main");
		setIsScanning(false);
		setScanProgress({ status: "idle", message: "" });
		setScanResult(null);
	};

	const getStatusIcon = () => {
		switch (scanProgress.status) {
			case "scanning":
				return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
			case "completed":
				return <CheckCircle className="h-5 w-5 text-green-500" />;
			case "failed":
				return <XCircle className="h-5 w-5 text-red-500" />;
			default:
				return null;
		}
	};

	return (
		<div className="max-w-4xl mx-auto space-y-6">
			{/* Header */}
			<div>
				<h1 className="text-3xl font-bold text-gray-900">
					Manual Security Scan
				</h1>
				<p className="text-gray-600 mt-2">
					Trigger a comprehensive security scan on any GitHub repository
				</p>
			</div>

			{/* Scan Form */}
			<div className="bg-white rounded-lg shadow-sm">
				<div className="px-6 py-4 border-b border-gray-200">
					<h3 className="text-lg font-semibold text-gray-900 flex items-center">
						<Search className="h-5 w-5 mr-2" />
						Repository Scan
					</h3>
				</div>

				<form onSubmit={startScan} className="p-6 space-y-6">
					<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div className="md:col-span-2">
							<label
								htmlFor="repoName"
								className="block text-sm font-medium text-gray-700 mb-2"
							>
								Repository Name
							</label>
							<div className="relative">
								<input
									type="text"
									id="repoName"
									value={repoName}
									onChange={(e) => setRepoName(e.target.value)}
									placeholder="owner/repository-name"
									className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 pl-10"
									disabled={isScanning}
									required
								/>
								<div className="absolute inset-y-0 left-0 pl-3 flex items-center">
									<GitBranch className="h-5 w-5 text-gray-400" />
								</div>
							</div>
							<p className="mt-1 text-xs text-gray-500">
								Format: username/repo-name (e.g., octocat/Hello-World)
							</p>
						</div>

						<div>
							<label
								htmlFor="branch"
								className="block text-sm font-medium text-gray-700 mb-2"
							>
								Branch
							</label>
							<input
								type="text"
								id="branch"
								value={branch}
								onChange={(e) => setBranch(e.target.value)}
								placeholder="main"
								className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
								disabled={isScanning}
							/>
						</div>
					</div>

					<div className="flex items-center justify-between">
						<div className="flex space-x-3">
							<button
								type="submit"
								disabled={isScanning || !repoName.trim()}
								className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
							>
								{isScanning ? (
									<>
										<Loader2 className="h-4 w-4 mr-2 animate-spin" />
										Scanning...
									</>
								) : (
									<>
										<Search className="h-4 w-4 mr-2" />
										Start Scan
									</>
								)}
							</button>

							{(scanProgress.status === "completed" ||
								scanProgress.status === "failed") && (
								<button
									type="button"
									onClick={resetForm}
									className="btn-secondary flex items-center"
								>
									<RefreshCw className="h-4 w-4 mr-2" />
									New Scan
								</button>
							)}
						</div>

						{scanProgress.status !== "idle" && (
							<div className="flex items-center space-x-2">
								{getStatusIcon()}
								<span className="text-sm text-gray-600">
									{scanProgress.message}
								</span>
							</div>
						)}
					</div>
				</form>
			</div>

			{/* Progress/Results */}
			{scanProgress.status !== "idle" && (
				<div className="bg-white rounded-lg shadow-sm">
					<div className="px-6 py-4 border-b border-gray-200">
						<h3 className="text-lg font-semibold text-gray-900 flex items-center">
							<Clock className="h-5 w-5 mr-2" />
							Scan Progress
						</h3>
					</div>

					<div className="p-6">
						{scanProgress.status === "scanning" && (
							<div className="text-center py-8">
								<div className="flex justify-center mb-4">
									<Loader2 className="h-12 w-12 animate-spin text-blue-500" />
								</div>
								<h4 className="text-lg font-medium text-gray-900 mb-2">
									Security Scan in Progress
								</h4>
								<p className="text-gray-600 mb-6">{scanProgress.message}</p>

								<div className="bg-gray-50 rounded-lg p-4 max-w-2xl mx-auto">
									<div className="space-y-3">
										<div className="flex items-center text-sm text-gray-600">
											<div className="h-2 w-2 bg-blue-500 rounded-full mr-3 animate-pulse"></div>
											Cloning repository...
										</div>
										<div className="flex items-center text-sm text-gray-600">
											<div className="h-2 w-2 bg-blue-500 rounded-full mr-3 animate-pulse"></div>
											Running security analysis...
										</div>
										<div className="flex items-center text-sm text-gray-600">
											<div className="h-2 w-2 bg-gray-300 rounded-full mr-3"></div>
											Generating AI insights...
										</div>
										<div className="flex items-center text-sm text-gray-600">
											<div className="h-2 w-2 bg-gray-300 rounded-full mr-3"></div>
											Creating GitHub issue...
										</div>
									</div>
								</div>
							</div>
						)}

						{scanProgress.status === "completed" && scanProgress.details && (
							<div className="text-center py-8">
								<div className="flex justify-center mb-4">
									<CheckCircle className="h-12 w-12 text-green-500" />
								</div>
								<h4 className="text-lg font-medium text-gray-900 mb-2">
									Scan Completed Successfully!
								</h4>
								<p className="text-gray-600 mb-6">{scanProgress.message}</p>

								<div className="bg-green-50 rounded-lg p-6 max-w-2xl mx-auto">
									<div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
										<div>
											<div className="text-2xl font-bold text-gray-900">
												{scanProgress.details.total_findings || 0}
											</div>
											<div className="text-sm text-gray-600">Total Issues</div>
										</div>
										<div>
											<div className="text-2xl font-bold text-red-600">
												{scanProgress.details.critical_count || 0}
											</div>
											<div className="text-sm text-gray-600">Critical</div>
										</div>
										<div>
											<div className="text-2xl font-bold text-yellow-600">
												{scanProgress.details.high_count || 0}
											</div>
											<div className="text-sm text-gray-600">High</div>
										</div>
										<div>
											<div className="text-2xl font-bold text-blue-600">
												{scanProgress.details.medium_count || 0}
											</div>
											<div className="text-sm text-gray-600">Medium</div>
										</div>
									</div>

									<div className="mt-6 flex justify-center space-x-3">
										<a href="/scans" className="btn-primary text-sm">
											View Scan Results
										</a>
										<a
											href={`https://github.com/${repoName}/issues`}
											target="_blank"
											rel="noopener noreferrer"
											className="btn-secondary text-sm flex items-center"
										>
											View GitHub Issues
											<ExternalLink className="ml-1 h-4 w-4" />
										</a>
									</div>
								</div>
							</div>
						)}

						{scanProgress.status === "failed" && (
							<div className="text-center py-8">
								<div className="flex justify-center mb-4">
									<XCircle className="h-12 w-12 text-red-500" />
								</div>
								<h4 className="text-lg font-medium text-gray-900 mb-2">
									Scan Failed
								</h4>
								<p className="text-gray-600 mb-6">{scanProgress.message}</p>

								{scanResult?.error && (
									<div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto mb-6">
										<div className="flex items-center">
											<AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
											<p className="text-sm text-red-700">{scanResult.error}</p>
										</div>
									</div>
								)}

								<button onClick={resetForm} className="btn-primary">
									Try Again
								</button>
							</div>
						)}
					</div>
				</div>
			)}

			{/* Instructions */}
			<div className="bg-blue-50 rounded-lg p-6">
				<h4 className="text-lg font-medium text-blue-900 mb-3">How it works</h4>
				<div className="space-y-2 text-sm text-blue-800">
					<div className="flex items-start space-x-2">
						<span className="font-medium">1.</span>
						<span>
							Enter the repository name (must be accessible with your GitHub
							token)
						</span>
					</div>
					<div className="flex items-start space-x-2">
						<span className="font-medium">2.</span>
						<span>
							Watchman clones the repository and runs Semgrep security analysis
						</span>
					</div>
					<div className="flex items-start space-x-2">
						<span className="font-medium">3.</span>
						<span>
							Claude AI analyzes findings and provides intelligent insights
						</span>
					</div>
					<div className="flex items-start space-x-2">
						<span className="font-medium">4.</span>
						<span>
							A detailed GitHub issue is created with specific remediation steps
						</span>
					</div>
				</div>
			</div>
		</div>
	);
}
