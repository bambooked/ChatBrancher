import type {
	LoginRequest,
	TokenResponse,
	ChatResponse,
	ChatTreeResponse,
	SendMessageRequest,
	SendMessageResponse
} from '$lib/types/api';

export class ApiClient {
	constructor(private baseUrl: string) {}

	async login(request: LoginRequest): Promise<TokenResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`Login failed: ${response.status}`);
		}

		return response.json();
	}

	async getChats(token: string): Promise<ChatResponse[]> {
		const response = await fetch(`${this.baseUrl}/api/v1/chats`, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch chats: ${response.status}`);
		}

		return response.json();
	}

	async getChatTree(chatUuid: string, token: string): Promise<ChatTreeResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/chats/${chatUuid}`, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch chat tree: ${response.status}`);
		}

		return response.json();
	}

	async sendMessage(
		chatUuid: string,
		request: SendMessageRequest,
		token: string
	): Promise<SendMessageResponse> {
		const response = await fetch(`${this.baseUrl}/api/v1/chats/${chatUuid}/messages`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`Failed to send message: ${response.status}`);
		}

		return response.json();
	}
}
