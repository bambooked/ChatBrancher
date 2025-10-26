// API型定義

export interface LoginRequest {
	username: string;
	password: string;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UserResponse {
	uuid: string;
	username: string;
	email: string;
	is_active: boolean;
}

export interface ChatResponse {
	uuid: string;
	owner_uuid: string;
	created: string;
	updated: string;
}

export interface MessageResponse {
	uuid: string;
	role: string;
	content: string;
	parent_uuid: string | null;
	created_at: string;
	updated_at: string;
}

export interface ChatTreeResponse {
	uuid: string;
	owner_uuid: string;
	created: string;
	updated: string;
	messages: MessageResponse[];
}

export interface SendMessageRequest {
	content: string;
	parent_message_uuid: string | null;
	llm_model?: string;
}

export interface SendMessageResponse {
	user_message: MessageResponse;
	assistant_message: MessageResponse;
}

export interface TreeNode extends MessageResponse {
	children: TreeNode[];
}
