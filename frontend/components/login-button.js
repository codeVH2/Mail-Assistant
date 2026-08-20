const BACKEND_API = process.env.NEXT_PUBLIC_BACKEND_API;

export default function LoginButton() {
  return (
    <a href={`${BACKEND_API}/auth/gmail`}>
      <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Login with Google
      </button>
    </a>
  );
}
