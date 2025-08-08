"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { Header } from "@/components/layout/header";

export default function LearningHubRedirect() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading } = useAuth();
    const { schools, isLoading: schoolsLoading } = useSchools();

    useEffect(() => {
        // Wait for auth and schools to load
        if (authLoading || schoolsLoading) return;

        // If not authenticated, redirect to login
        if (!isAuthenticated) {
            router.push('/login');
            return;
        }

        // If we have schools, redirect to the first school's hubs
        if (schools && schools.length > 0) {
            // Use the first school the user has access to
            const defaultSchool = schools[0];
            router.push(`/school/${defaultSchool.id}/hubs`);
            return;
        }

        // If no schools, redirect to home
        router.push('/');
    }, [authLoading, schoolsLoading, isAuthenticated, schools, router]);

    // Show loading while determining where to redirect
    return (
        <>
            <Header />
            <div className="min-h-screen bg-black text-white">
                <div className="flex justify-center items-center py-12">
                    <div className="text-center">
                        <div className="w-12 h-12 border-t-2 border-b-2 border-white rounded-full animate-spin mx-auto mb-4"></div>
                        <p className="text-gray-400">Redirecting to Learning Hubs...</p>
                    </div>
                </div>
            </div>
        </>
    );
}
