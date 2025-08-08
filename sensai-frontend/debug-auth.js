console.log('=== Debug Auth Configuration ===');
console.log('NEXTAUTH_URL:', process.env.NEXTAUTH_URL);
console.log('GOOGLE_CLIENT_ID:', process.env.GOOGLE_CLIENT_ID);
console.log('GOOGLE_CLIENT_SECRET:', process.env.GOOGLE_CLIENT_SECRET ? 'SET' : 'NOT SET');
console.log('Expected callback URL:', `${process.env.NEXTAUTH_URL}/api/auth/callback/google`);
console.log('=== End Debug ===');
