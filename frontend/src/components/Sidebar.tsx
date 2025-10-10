"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
	Shield,
	Activity,
	Search,
	Settings,
	BarChart3,
	AlertTriangle,
	Clock,
	Database,
} from "lucide-react";
import { clsx } from "clsx";

const navigation = [
	{
		name: "Dashboard",
		href: "/",
		icon: BarChart3,
		description: "Overview and statistics",
	},
	{
		name: "Recent Scans",
		href: "/scans",
		icon: Activity,
		description: "View scan history",
	},
	{
		name: "Manual Scan",
		href: "/scan",
		icon: Search,
		description: "Trigger new scans",
	},
	{
		name: "Alerts",
		href: "/alerts",
		icon: AlertTriangle,
		description: "Security alerts",
	},
	{
		name: "System Status",
		href: "/status",
		icon: Database,
		description: "Health monitoring",
	},
];

export function Sidebar() {
	const pathname = usePathname();

	return (
		<div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
			{/* Logo */}
			<div className="flex h-16 items-center px-6 border-b border-gray-200">
				<div className="flex items-center space-x-3">
					<div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
						<Shield className="h-6 w-6 text-white" />
					</div>
					<div>
						<h1 className="text-xl font-bold text-gray-900">Watchman</h1>
						<p className="text-xs text-gray-500">Security Platform</p>
					</div>
				</div>
			</div>

			{/* Navigation */}
			<nav className="mt-6 px-3">
				<ul className="space-y-2">
					{navigation.map((item) => {
						const isActive = pathname === item.href;
						return (
							<li key={item.name}>
								<Link
									href={item.href}
									className={clsx(
										"group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
										isActive
											? "bg-primary-50 text-primary-700 border-r-2 border-primary-600"
											: "text-gray-700 hover:bg-gray-50 hover:text-gray-900",
									)}
								>
									<item.icon
										className={clsx(
											"mr-3 h-5 w-5 flex-shrink-0",
											isActive
												? "text-primary-600"
												: "text-gray-400 group-hover:text-gray-600",
										)}
									/>
									<div className="flex-1">
										<div className="font-medium">{item.name}</div>
										<div className="text-xs text-gray-500 mt-0.5">
											{item.description}
										</div>
									</div>
								</Link>
							</li>
						);
					})}
				</ul>
			</nav>

			{/* Status Indicator */}
			<div className="absolute bottom-6 left-3 right-3">
				<div className="rounded-lg bg-gray-50 p-3">
					<div className="flex items-center space-x-3">
						<div className="flex-shrink-0">
							<div className="flex h-8 w-8 items-center justify-center rounded-full bg-success-100">
								<div className="h-2 w-2 rounded-full bg-success-500 animate-pulse"></div>
							</div>
						</div>
						<div className="flex-1 min-w-0">
							<p className="text-sm font-medium text-gray-900">System Online</p>
							<p className="text-xs text-gray-500">All services running</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
