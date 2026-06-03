# ai-inquiry-support-app

問い合わせを管理し、AI による自動分類と運用メトリクスの集計を行う学習用 Web アプリケーションです。
**SQL・ログ分析・AI 活用・メトリクス設計** を実践的に学ぶことを目的に、Phase ごとに小さく実装を積み上げています。

## 1. アプリ概要

ユーザーからの問い合わせを保存し、OpenAI API で自動分類（カテゴリ・緊急度）を行うバックエンド API です。
さらに、すべての操作を `event_logs` テーブルに記録し、その集計結果を `GET /metrics` で確認できます。

- 問い合わせの登録・AI 分類
- 操作イベントのログ記録
- イベントログを SQL で集計した運用メトリクス API

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

## 5. API 一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/health` | DB 疎通確認 |
| POST | `/inquiries` | 問い合わせを作成 |
| POST | `/inquiries/{id}/classify` | 問い合わせを AI 分類 |
| GET | `/metrics` | イベントログの集計メトリクスを取得 |

API 仕様は起動後に http://localhost:8000/docs （Swagger UI）で確認できます。

## 6. DB テーブル概要

### `inquiries` — 問い合わせ
| カラム | 型 | 説明 |
|---|---|---|
| id | int | 主キー |
| body | text | 問い合わせ本文 |
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

存在しない問い合わせへの分類リクエストは、外部キー制約に違反しないよう `inquiry_id` を NULL にし、
指定 ID を `detail` に残しています。

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

# 問い合わせを分類（OpenAI 設定が必要）
curl -X POST http://localhost:8000/inquiries/1/classify

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
- **段階的な開発**: Phase ごとに小さく動く単位で実装を積み上げる進め方

## ファイル構成

- `app/main.py`: FastAPI のルート定義
- `app/database.py`: SQLAlchemy のエンジン / セッション設定
- `app/models.py`: SQLAlchemy モデル
- `app/schemas.py`: Pydantic スキーマ
- `app/crud.py`: DB 操作（書き込み・集計）
- `app/ai_classifier.py`: OpenAI API による分類処理
- `docker-compose.yml`: PostgreSQL サービス定義
- `.env.example`: 環境変数のサンプル
- `requirements.txt`: Python 依存パッケージ
