import pytest
from domain.services.chat_tree_structure import ChatStructure


class TestChatStructureBehavior:
    """ChatStructureの振る舞いをテスト - 実装詳細ではなくビジネス要件に焦点を当てる"""

    def test_conversation_branching_scenario(self):
        """会話が分岐するシナリオ：ユーザーが過去のメッセージから別の返答を試す場合"""
        # Given: システムメッセージから始まる会話
        chat = ChatStructure(message_uuid="system-welcome")
        
        # When: ユーザーが質問し、アシスタントが回答
        chat.append_message("system-welcome", "user-hello")
        chat.append_message("user-hello", "assistant-greeting")
        
        # And: ユーザーが同じ質問から別の文脈で会話を続ける（分岐）
        chat.append_message("user-hello", "assistant-different-response")
        
        # Then: それぞれの会話パスが独立して取得できる
        path1 = chat.load_flatten_history("assistant-greeting")
        path2 = chat.load_flatten_history("assistant-different-response")
        
        assert path1 == ["system-welcome", "user-hello", "assistant-greeting"]
        assert path2 == ["system-welcome", "user-hello", "assistant-different-response"]
        assert path1 != path2  # 異なる会話の流れ

    def test_conversation_continuation_from_any_point(self):
        """任意の時点から会話を継続できることを確認"""
        # Given: 既存の会話履歴
        chat = ChatStructure(message_uuid="msg-1")
        chat.append_message("msg-1", "msg-2")
        chat.append_message("msg-2", "msg-3")
        chat.append_message("msg-3", "msg-4")
        
        # When: 途中のメッセージから新しい分岐を作成
        chat.append_message("msg-2", "msg-5")  # msg-2から分岐
        
        # Then: 新しい分岐の履歴が正しく取得できる
        new_branch_history = chat.load_flatten_history("msg-5")
        assert new_branch_history == ["msg-1", "msg-2", "msg-5"]
        
        # And: 元の会話履歴も保持されている
        original_history = chat.load_flatten_history("msg-4")
        assert original_history == ["msg-1", "msg-2", "msg-3", "msg-4"]

    def test_message_lookup_regardless_of_depth(self):
        """メッセージの深さに関わらず、任意のメッセージを検索できる"""
        # Given: 複雑な分岐を持つ会話ツリー
        chat = ChatStructure(message_uuid="root")
        
        # 深い階層と複数の分岐を作成
        messages_to_find = []
        for branch in ["A", "B", "C"]:
            parent = "root"
            for depth in range(5):
                msg_id = f"{branch}-{depth}"
                chat.append_message(parent, msg_id)
                messages_to_find.append(msg_id)
                parent = msg_id
        
        # When/Then: すべてのメッセージが検索可能
        for msg_id in messages_to_find:
            found = chat.pick_message_from_uuid(msg_id)
            assert found is not None
            assert found.message_uuid == msg_id

    def test_nonexistent_message_handling(self):
        """存在しないメッセージの処理が適切にエラーになる"""
        chat = ChatStructure(message_uuid="root")
        
        with pytest.raises(ValueError, match="条件に一致するノードが見つかりませんでした"):
            chat.pick_message_from_uuid("does-not-exist")

    def test_conversation_persistence_and_restoration(self):
        """会話ツリーの永続化と復元が正しく動作する"""
        # Given: 実際の会話シナリオ
        original_chat = ChatStructure(message_uuid="system-init")
        
        # ユーザーとの会話
        original_chat.append_message("system-init", "user-question-1")
        original_chat.append_message("user-question-1", "assistant-answer-1")
        original_chat.append_message("assistant-answer-1", "user-followup")
        original_chat.append_message("user-followup", "assistant-clarification")
        
        # 別の分岐
        original_chat.append_message("user-question-1", "assistant-alternative-answer")
        
        # When: シリアライズして復元
        serialized = original_chat.to_dict()
        restored_chat = ChatStructure.from_dict(serialized)
        
        # Then: 復元後も同じ会話履歴が取得できる
        original_path = original_chat.load_flatten_history("assistant-clarification")
        restored_path = restored_chat.load_flatten_history("assistant-clarification")
        assert original_path == restored_path
        
        # And: 分岐も正しく復元される
        original_branch = original_chat.load_flatten_history("assistant-alternative-answer")
        restored_branch = restored_chat.load_flatten_history("assistant-alternative-answer")
        assert original_branch == restored_branch

    def test_prevents_orphaned_messages(self):
        """親が存在しないメッセージの追加を防ぐ"""
        chat = ChatStructure(message_uuid="root")
        
        # 存在しない親にメッセージを追加しようとする
        with pytest.raises(ValueError):
            chat.append_message("non-existent-parent", "orphan-message")

    def test_supports_llm_retry_scenario(self):
        """LLMの再生成シナリオ：同じユーザーメッセージに対して複数の回答を生成"""
        chat = ChatStructure(message_uuid="system")
        
        # ユーザーが質問
        chat.append_message("system", "user-complex-question")
        
        # LLMが複数回回答を生成（再試行シナリオ）
        chat.append_message("user-complex-question", "llm-response-v1")
        chat.append_message("user-complex-question", "llm-response-v2")
        chat.append_message("user-complex-question", "llm-response-v3")
        
        # それぞれの回答への会話履歴が独立して取得できる
        histories = [
            chat.load_flatten_history("llm-response-v1"),
            chat.load_flatten_history("llm-response-v2"),
            chat.load_flatten_history("llm-response-v3")
        ]
        
        # すべて同じ質問から分岐している
        for history in histories:
            assert history[:2] == ["system", "user-complex-question"]
            
        # しかし異なる回答を含んでいる
        assert len(set(h[-1] for h in histories)) == 3