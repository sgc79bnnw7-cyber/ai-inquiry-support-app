# ai-inquiry-support-app

問い合わせを管理し、AI による自動分類と運用メトリクスの集計を行う学習用 Web アプリケーションです。
**SQL・ログ分析・AI 活用・メトリクス設計** を実践的に学ぶことを目的に、Phase ごとに小さく実装を積み上げています。

## 1. アプリ概要

ユーザーからの問い合わせを保存し、OpenAI API で自動分類（カテゴリ・緊急度）を行うバックエンド API です。
さらに、すべての操作を `event_logs` テーブルに記録し、その集計結果を `GET /metrics` で確認できます。

- 問い合わせの登録・AI 分類
- 操作イベントのログ記録
- イベントログを SQL で集計した運用メトリクス API
- 問い合わせ一覧と対応ステータス管理（簡易管理画面）

## 2. 学習目的

このプロジェクトは、以下を実践的に学ぶために作成しました。

- **SQL**: PostgreSQL でのテーブル設計と集計クエリ（`FILTER` 句による条件付き集計）
- **ログ分析**: 操作イベントを記録し、SQL で後から分析できるログ設計
- **AI 活用**: OpenAI API を使った問い合わせの自動分類
- **メトリクス設計**: ログから運用指標（成功率など）を導出する集計 API
- **クラウド / インフラ**: Docker Compose による DB 環境構築

## 3. 技術スタック

| 分類 | 技術 |
|---|---|
| 言語 | Python 3.12 |
| フレームワーク | FastAPI |
| DB | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| スキーマ | Pydantic v2 |
| AI | OpenAI API |
| インフラ | Docker Compose |

## 4. 実装済み機能（Phase 別）

小さく動く単位で段階的に実装してきました。

- **Phase 1** — 基盤構築: FastAPI 起動、PostgreSQL（Docker Compose）、`GET /health`、`POST /inquiries`
- **Phase 2** — AI 分類 MVP: `POST /inquiries/{id}/classify`、`ai_classifications` テーブル
- **Phase 3** — ログ設計: `event_logs` テーブル、問い合わせ作成・分類リクエストのイベント記録
- **Phase 4** — メトリクス: `GET /metrics`、`event_logs` を SQL 集計した運用指標
- **Phase 5** — 問い合わせ管理: 一覧表示・対応ステータス管理・簡易管理画面UI
  - `GET /inquiries`（最新 AI 分類つきの一覧）
  - `PATCH /inquiries/{id}/status`（対応状況の更新）
  - `inquiries.status` カラム追加（手動 ALTER TABLE で反映）
  - `status_changed` イベントログの記録
  - 日本語ダッシュボードUI（一覧テーブル・ステータス変更）
- **Phase 6** — 検索・フィルター機能: 一覧をステータス / カテゴリ / 緊急度 / キーワードで絞り込み
  - `GET /inquiries` にクエリパラメータ（`status` / `category` / `urgency` / `keyword`）を追加
  - キーワードは本文の部分一致（`ILIKE`）、カテゴリ・緊急度は「最新の AI 分類」で絞り込み
  - UI に検索・フィルター欄と「条件をリセット」ボタンを追加
- **Phase 7** — AI返信案生成: 問い合わせ本文から一次返信の下書きを AI 生成
  - `POST /inquiries/{id}/reply-draft`（返信案を生成して返す）
  - 最新 AI 分類があればカテゴリ・緊急度も文脈として参考にする
  - 返信案は DB 保存せず、`reply_draft_generated` イベントログのみ記録
  - UI から生成し、コピー可能な下書きとして表示

## 5. API 一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | 日本語の簡易ダッシュボードUI |
| GET | `/health` | DB 疎通確認 |
| POST | `/inquiries` | 問い合わせを作成 |
| GET | `/inquiries` | 問い合わせ一覧を取得（最新 AI 分類つき・絞り込み可） |
| POST | `/inquiries/{id}/classify` | 問い合わせを AI 分類 |
| PATCH | `/inquiries/{id}/status` | 対応ステータスを更新 |
| POST | `/inquiries/{id}/reply-draft` | AI 返信案（下書き）を生成 |
| GET | `/metrics` | イベントログの集計メトリクスを取得 |

`GET /inquiries` は、次の任意クエリパラメータで絞り込めます（すべて省略可。無指定なら全件）。

| パラメータ | 説明 |
|---|---|
| `status` | 対応状況で絞り込み（`new` / `in_progress` / `closed`） |
| `category` | 最新 AI 分類のカテゴリで絞り込み（`login` / `billing` / `technical_issue` / `how_to_use` / `other`） |
| `urgency` | 最新 AI 分類の緊急度で絞り込み（`high` / `medium` / `low`） |
| `keyword` | 問い合わせ本文の部分一致検索（大文字小文字を区別しない） |

複数指定すると AND 条件で絞り込まれます（例: `?status=new&category=login`）。

API 仕様は起動後に http://localhost:8000/docs （Swagger UI）で確認できます。
ブラウザで http://localhost:8000/ を開くと、日本語の簡易管理画面が利用できます。
ダッシュボードUIでは次の操作ができます。

- 問い合わせの登録・AI 分類の実行
- 問い合わせ一覧の表示と対応ステータスの変更
- 一覧の絞り込み（ステータス / カテゴリ / 緊急度 / キーワード）と条件リセット
- AI 返信案の生成（問い合わせ ID を指定）。結果はコピー可能な textarea で表示し、API キー未設定時は日本語でエラー表示
- 運用メトリクスの確認

## 6. DB テーブル概要

### `inquiries` — 問い合わせ
| カラム | 型 | 説明 |
|---|---|---|
| id | int | 主キー |
| body | text | 問い合わせ本文 |
| status | varchar | 対応状況（new / in_progress / closed、既定 `new`） |
| created_at | timestamptz | 作成日時 |

### `ai_classifications` — AI 分類結果
| カラム | 型 | 説明 |
|---|---|---|
| id | int | 主キー |
| inquiry_id | int (FK) | 対象の問い合わせ |
| category | varchar | カテゴリ（login / billing / technical_issue / how_to_use / other） |
| urgency | varchar | 緊急度（low / medium / high） |
| reason | text | 分類理由 |
| model_name | varchar | 使用モデル名 |
| prompt_version | varchar | プロンプトバージョン |
| created_at | timestamptz | 作成日時 |

### `event_logs` — 操作イベントログ
| カラム | 型 | 説明 |
|---|---|---|
| id | int | 主キー |
| event_type | varchar | イベント種別 |
| inquiry_id | int (FK, NULL可) | 関連する問い合わせ（無い場合は NULL） |
| status | varchar | success / error |
| detail | text (NULL可) | エラー詳細など |
| created_at | timestamptz | 記録日時 |

`ai_classifications` と `event_logs` は `inquiry_id` で `inquiries` を参照します。

## 7. ログ設計

操作のたびに `event_logs` へ 1 行記録します。`event_type` と `status` を分けて持つことで、
テーブル設計を変えずに SQL だけで様々な集計・分析ができる構造にしています。

| event_type | status | 記録タイミング |
|---|---|---|
| `inquiry_created` | success | 問い合わせ作成成功時 |
| `classification_requested` | success | 分類リクエスト時（対象の問い合わせが存在） |
| `classification_requested` | error | 分類リクエスト時（対象が存在せず 404、`inquiry_id` は NULL） |
| `classification_completed` | success | AI 分類成功時 |
| `classification_completed` | error | AI 分類失敗時（`detail` にエラー内容） |
| `status_changed` | success | 対応ステータス更新成功時（`detail` に `new -> in_progress` のように遷移を記録） |
| `status_changed` | error | 更新失敗時（存在しないID・不正な値など、`detail` に理由） |
| `reply_draft_generated` | success | AI 返信案の生成成功時（`detail` に参考にした `category` / `urgency`） |
| `reply_draft_generated` | error | 生成失敗時（存在しないID・API キー未設定など、`detail` に理由） |

存在しない問い合わせへの分類リクエストやステータス更新は、外部キー制約に違反しないよう `inquiry_id` を NULL にし、
指定 ID を `detail` に残しています。`status_changed` の `detail` に「旧 → 新」を残すことで、
後から SQL でステータス遷移や対応状況の集計・分析ができます。

## 8. メトリクス設計

`GET /metrics` は `event_logs` を 1 クエリで集計し、運用指標を返します。
PostgreSQL の `COUNT(*) FILTER (WHERE ...)` を使い、複数の集計値を 1 回のクエリで取得しています。

レスポンス例:

```json
{
  "total_inquiries": 3,
  "classified_count": 2,
  "classification_success_count": 0,
  "classification_error_count": 2,
  "classification_success_rate": 0.0
}
```

- `classification_success_rate` は成功率（%）。試行が 0 件のときはゼロ除算を避けて `0.0` を返します。

## 9. 起動手順

### 1. 環境変数ファイルを用意

```bash
cp .env.example .env
```

`.env` には DB 接続 URL と OpenAI の設定（`OPENAI_API_KEY` / `OPENAI_MODEL`）を記述します。
**API キーなどの実値はコミットしないでください。** AI 分類を使わない場合はキーは空のままで問題ありません。

### 2. PostgreSQL を起動

```bash
docker compose up -d
```

### 2-1. 既存DBに status カラムを追加（既存環境のみ）

このアプリは Alembic を使わず、起動時に `Base.metadata.create_all()` でテーブルを作成します。
`create_all()` は**新規テーブルは作りますが、既存テーブルへのカラム追加は行いません**。
そのため、Phase 5 より前から動かしていた既存DBには、手動で `status` カラムを追加します。

```bash
docker compose exec db psql -U app_user -d ai_inquiry_support \
  -c "ALTER TABLE inquiries ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'new';"
```

> はじめてDBを作成する場合（テーブルが空の状態）は、`create_all()` が `status` 付きで
> `inquiries` を作成するため、この手順は不要です。
> （将来 Alembic を導入すると、こうしたカラム追加を自動で管理できます。）

### 3. 依存関係をインストール

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. API を起動

```bash
uvicorn app.main:app --reload
```

## 10. 動作確認手順

```bash
# 疎通確認
curl http://localhost:8000/health

# 問い合わせを作成
curl -X POST http://localhost:8000/inquiries \
  -H "Content-Type: application/json" \
  -d '{"body":"ログインができません"}'

# 問い合わせ一覧を取得（最新 AI 分類つき）
curl http://localhost:8000/inquiries

# 一覧を絞り込む（検索・フィルター）
curl "http://localhost:8000/inquiries?status=new"
curl "http://localhost:8000/inquiries?keyword=ログイン"
curl "http://localhost:8000/inquiries?category=login&urgency=high"

# 問い合わせを分類（OpenAI 設定が必要）
curl -X POST http://localhost:8000/inquiries/1/classify

# 対応ステータスを更新（new / in_progress / closed）
curl -X PATCH http://localhost:8000/inquiries/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# AI 返信案（下書き）を生成（OpenAI 設定が必要）
curl -X POST http://localhost:8000/inquiries/1/reply-draft

# メトリクスを確認
curl http://localhost:8000/metrics
```

PostgreSQL のテーブル・ログを直接確認する場合:

```bash
docker compose exec db psql -U app_user -d ai_inquiry_support -c "SELECT * FROM event_logs ORDER BY id;"
```

## 11. このプロジェクトで学べること

- **問い合わせ管理 API の設計**: FastAPI + PostgreSQL での REST API とデータモデリング
- **AI の組み込み**: OpenAI API による問い合わせの自動分類と、結果の永続化
- **ログ設計**: 後から SQL で分析しやすい `event_logs` の設計（`event_type` × `status`）
- **SQL 集計**: `FILTER` 句を使った条件付き集計で、ログから運用指標を 1 クエリで導出
- **メトリクス API**: ログを集計して成功率などを返す `/metrics` の実装
- **状態管理**: 問い合わせに対応ステータス（new / in_progress / closed）を持たせ、遷移を管理する設計
- **ログ設計（状態遷移）**: ステータス変更を `status_changed` として記録し、後から分析できる形にする
- **手動マイグレーション**: `create_all()` の限界を理解し、`ALTER TABLE` で既存DBにカラムを追加（Alembic が必要になる理由を体験）
- **最新分類結果の取得**: `DISTINCT ON` を使い「問い合わせごとの最新の AI 分類」を 1 件だけ取得
- **問い合わせ管理画面の実装**: 一覧表示・ステータス変更ができる日本語の簡易管理画面（HTML/CSS/JS）
- **動的 WHERE 条件**: 指定された絞り込み条件だけを AND で積み上げてクエリを組み立てる
- **部分一致検索**: `ILIKE '%keyword%'` による大文字小文字を区別しない本文検索
- **最新分類へのフィルタリング**: 古い分類で誤ヒットせず、最新の AI 分類に対して絞り込む設計
- **後方互換な API 拡張**: 既存のレスポンス形式や無指定時の挙動を保ったままパラメータを追加
- **フィルタ状態管理**: 素の JavaScript で絞り込み条件を一元管理し、更新後も条件を維持する
- **AI による返信文生成**: 問い合わせ本文から、担当者向けの一次返信の下書きを生成
- **分類結果のプロンプト再利用**: 既存の AI 分類（カテゴリ・緊急度）を返信生成の文脈として渡す設計
- **構造化出力と自由文生成の使い分け**: 分類は Pydantic スキーマで構造化、返信は自由文という用途別の使い分け
- **保存しない設計判断**: 再生成できる下書きは DB 保存せず、生成した事実だけをログに残すトレードオフ
- **AI 処理のログ設計**: 分類・返信生成の成功 / 失敗を `event_logs` に統一形式で記録
- **段階的な開発**: Phase ごとに小さく動く単位で実装を積み上げる進め方

## ファイル構成

- `app/main.py`: FastAPI のルート定義
- `app/database.py`: SQLAlchemy のエンジン / セッション設定
- `app/models.py`: SQLAlchemy モデル
- `app/schemas.py`: Pydantic スキーマ
- `app/crud.py`: DB 操作（書き込み・集計）
- `app/ai_classifier.py`: OpenAI API による分類処理
- `app/ai_reply.py`: OpenAI API による返信案（下書き）生成
- `app/static/`: 日本語ダッシュボードUI（`index.html` / `style.css` / `app.js`）
- `docker-compose.yml`: PostgreSQL サービス定義
- `.env.example`: 環境変数のサンプル
- `requirements.txt`: Python 依存パッケージ
