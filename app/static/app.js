"use strict";

// ===== 問い合わせ登録 =====
const createBtn = document.getElementById("create-btn");
const bodyInput = document.getElementById("inquiry-body");
const createResult = document.getElementById("create-result");
const classifyIdInput = document.getElementById("classify-id");

// 結果欄に成功/失敗メッセージを表示する
function showResult(el, type, html) {
  el.hidden = false;
  el.className = `result ${type}`;
  el.innerHTML = html;
}

async function createInquiry() {
  const body = bodyInput.value.trim();

  // 空欄チェック
  if (body === "") {
    showResult(
      createResult,
      "error",
      "問い合わせ内容を入力してください。"
    );
    return;
  }

  // 通信中はボタンを無効化（二重送信防止）
  createBtn.disabled = true;
  createBtn.textContent = "登録中...";

  try {
    const res = await fetch("/inquiries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body }),
    });

    if (!res.ok) {
      let detail = `エラーが発生しました（HTTP ${res.status}）`;
      try {
        const errData = await res.json();
        if (errData.detail) {
          detail = `登録に失敗しました：${JSON.stringify(errData.detail)}`;
        }
      } catch (_) {
        // JSON 以外のレスポンスはそのまま既定メッセージを使う
      }
      showResult(createResult, "error", detail);
      return;
    }

    const data = await res.json();

    // 成功表示
    showResult(
      createResult,
      "success",
      `問い合わせを登録しました。<br>` +
        `問い合わせID: <strong>${data.id}</strong><br>` +
        `内容: ${escapeHtml(data.body)}<br>` +
        `次は「2. AI分類を実行」でこのIDを使って分類できます（IDは自動入力済みです）。`
    );

    // 返ってきた id を AI分類エリアと返信案エリアの入力欄に自動入力
    classifyIdInput.value = data.id;
    replyIdInput.value = data.id;

    // 入力欄をクリアして次の入力をしやすくする
    bodyInput.value = "";

    // 登録によって件数・一覧が変わるので更新
    updateMetrics();
    updateList();
  } catch (err) {
    showResult(
      createResult,
      "error",
      `通信に失敗しました。サーバーが起動しているか確認してください。<br>詳細: ${escapeHtml(
        String(err)
      )}`
    );
  } finally {
    createBtn.disabled = false;
    createBtn.textContent = "問い合わせを登録";
  }
}

// HTML エスケープ（本文をそのまま表示すると崩れるため）
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

createBtn.addEventListener("click", createInquiry);

// ===== AI分類実行 =====
const classifyBtn = document.getElementById("classify-btn");
const classifyResult = document.getElementById("classify-result");

// カテゴリ・緊急度の日本語ラベル（表示を分かりやすくするため）
const CATEGORY_LABELS = {
  login: "ログイン",
  billing: "請求",
  technical_issue: "技術的な問題",
  how_to_use: "使い方",
  other: "その他",
};
const URGENCY_LABELS = {
  low: "低",
  medium: "中",
  high: "高",
};

// デバッグ用の詳細を小さく添える
function detailLine(text) {
  return `<br><span class="result-detail">詳細: ${escapeHtml(text)}</span>`;
}

async function classifyInquiry() {
  const idValue = classifyIdInput.value.trim();

  // 空欄チェック
  if (idValue === "") {
    showResult(
      classifyResult,
      "error",
      "inquiry_id（問い合わせ番号）を入力してください。"
    );
    return;
  }

  classifyBtn.disabled = true;
  classifyBtn.textContent = "分類中...";

  try {
    const res = await fetch(`/inquiries/${encodeURIComponent(idValue)}/classify`, {
      method: "POST",
    });

    // レスポンスを JSON として読む（失敗時の detail もここで取得）
    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }

    if (!res.ok) {
      const detail = data && data.detail ? String(data.detail) : "";

      // 404: 問い合わせが見つからない
      if (res.status === 404) {
        showResult(
          classifyResult,
          "error",
          "指定した問い合わせIDが見つかりません。" +
            "<br>先に「1. 問い合わせを登録」で問い合わせを作成してください。"
        );
        return;
      }

      // OpenAI APIキー未設定
      if (detail.includes("OPENAI_API_KEY is not set")) {
        showResult(
          classifyResult,
          "error",
          "OpenAI APIキーが未設定です。" +
            "<br>.env に OPENAI_API_KEY を設定するとAI分類を実行できます。" +
            detailLine(detail)
        );
        return;
      }

      // その他の失敗
      showResult(
        classifyResult,
        "error",
        "AI分類に失敗しました。" + (detail ? detailLine(detail) : "")
      );
      return;
    }

    // 成功表示
    const categoryLabel = CATEGORY_LABELS[data.category] || data.category;
    const urgencyLabel = URGENCY_LABELS[data.urgency] || data.urgency;

    showResult(
      classifyResult,
      "success",
      "AI分類が完了しました。<br>" +
        `<table class="result-table">` +
        `<tr><th>カテゴリ</th><td>${escapeHtml(categoryLabel)}（${escapeHtml(
          data.category
        )}）</td></tr>` +
        `<tr><th>緊急度</th><td>${escapeHtml(urgencyLabel)}（${escapeHtml(
          data.urgency
        )}）</td></tr>` +
        `<tr><th>理由</th><td>${escapeHtml(data.reason)}</td></tr>` +
        `<tr><th>使用モデル</th><td>${escapeHtml(data.model_name)}</td></tr>` +
        `<tr><th>プロンプトバージョン</th><td>${escapeHtml(
          data.prompt_version
        )}</td></tr>` +
        `</table>`
    );
  } catch (err) {
    showResult(
      classifyResult,
      "error",
      "通信に失敗しました。サーバーが起動しているか確認してください。" +
        detailLine(String(err))
    );
  } finally {
    classifyBtn.disabled = false;
    classifyBtn.textContent = "AI分類を実行";
    // 分類を実行したら（成功・失敗どちらでも）メトリクスと一覧を更新
    updateMetrics();
    updateList();
  }
}

classifyBtn.addEventListener("click", classifyInquiry);

// ===== AI返信案生成 =====
const replyBtn = document.getElementById("reply-btn");
const replyIdInput = document.getElementById("reply-id");
const replyResult = document.getElementById("reply-result");

// カテゴリ/緊急度を日本語ラベル付きで表す（null は「未分類」）
function labelOrNone(value, labels) {
  if (value === null || value === undefined) {
    return '<span class="muted">未分類</span>';
  }
  return `${escapeHtml(labels[value] || value)}（${escapeHtml(value)}）`;
}

async function generateReplyDraft() {
  const idValue = replyIdInput.value.trim();

  if (idValue === "") {
    showResult(
      replyResult,
      "error",
      "inquiry_id（問い合わせ番号）を入力してください。"
    );
    return;
  }

  replyBtn.disabled = true;
  replyBtn.textContent = "生成中...";

  try {
    const res = await fetch(
      `/inquiries/${encodeURIComponent(idValue)}/reply-draft`,
      { method: "POST" }
    );

    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }

    if (!res.ok) {
      const detail = data && data.detail ? String(data.detail) : "";

      if (res.status === 404) {
        showResult(
          replyResult,
          "error",
          "指定した問い合わせIDが見つかりません。" +
            "<br>先に「1. 問い合わせを登録」で問い合わせを作成してください。"
        );
        return;
      }

      if (detail.includes("OPENAI_API_KEY is not set")) {
        showResult(
          replyResult,
          "error",
          "OpenAI APIキーが未設定です。" +
            "<br>.env に OPENAI_API_KEY を設定するとAI返信案を生成できます。" +
            detailLine(detail)
        );
        return;
      }

      showResult(
        replyResult,
        "error",
        "AI返信案の生成に失敗しました。" + (detail ? detailLine(detail) : "")
      );
      return;
    }

    // 成功表示（返信案はコピーしやすいよう textarea に表示）
    showResult(
      replyResult,
      "success",
      "AI返信案を生成しました。内容を確認・編集してからご利用ください。<br>" +
        `<textarea class="reply-textarea" id="reply-text" readonly>${escapeHtml(
          data.reply_text
        )}</textarea>` +
        `<div class="actions"><button class="btn btn-sm" id="reply-copy-btn" type="button">コピー</button></div>` +
        `<table class="result-table">` +
        `<tr><th>使用モデル</th><td>${escapeHtml(data.model_name)}</td></tr>` +
        `<tr><th>プロンプトバージョン</th><td>${escapeHtml(
          data.prompt_version
        )}</td></tr>` +
        `<tr><th>参考カテゴリ</th><td>${labelOrNone(
          data.used_category,
          CATEGORY_LABELS
        )}</td></tr>` +
        `<tr><th>参考緊急度</th><td>${labelOrNone(
          data.used_urgency,
          URGENCY_LABELS
        )}</td></tr>` +
        `</table>`
    );

    // コピーボタンの動作を登録
    const copyBtn = document.getElementById("reply-copy-btn");
    const replyTextArea = document.getElementById("reply-text");
    copyBtn.addEventListener("click", () => {
      replyTextArea.select();
      navigator.clipboard
        .writeText(replyTextArea.value)
        .then(() => {
          copyBtn.textContent = "コピーしました";
          setTimeout(() => (copyBtn.textContent = "コピー"), 1500);
        })
        .catch(() => {
          copyBtn.textContent = "コピーできませんでした";
        });
    });
  } catch (err) {
    showResult(
      replyResult,
      "error",
      "通信に失敗しました。サーバーが起動しているか確認してください。" +
        detailLine(String(err))
    );
  } finally {
    replyBtn.disabled = false;
    replyBtn.textContent = "返信案を生成";
  }
}

replyBtn.addEventListener("click", generateReplyDraft);

// ===== メトリクス更新 =====
const metricsBtn = document.getElementById("metrics-btn");
const metricsResult = document.getElementById("metrics-result");
const mTotal = document.getElementById("m-total");
const mClassified = document.getElementById("m-classified");
const mSuccess = document.getElementById("m-success");
const mError = document.getElementById("m-error");
const mRate = document.getElementById("m-rate");

async function updateMetrics() {
  metricsBtn.disabled = true;
  metricsBtn.textContent = "更新中...";

  try {
    const res = await fetch("/metrics");
    if (!res.ok) {
      showResult(
        metricsResult,
        "error",
        `メトリクスの取得に失敗しました（HTTP ${res.status}）。`
      );
      return;
    }

    const data = await res.json();

    // カードに反映
    mTotal.textContent = data.total_inquiries;
    mClassified.textContent = data.classified_count;
    mSuccess.textContent = data.classification_success_count;
    mError.textContent = data.classification_error_count;
    mRate.textContent = `${data.classification_success_rate}%`;

    // 取得成功時はエラー表示を隠す
    metricsResult.hidden = true;
  } catch (err) {
    showResult(
      metricsResult,
      "error",
      "通信に失敗しました。サーバーが起動しているか確認してください。" +
        detailLine(String(err))
    );
  } finally {
    metricsBtn.disabled = false;
    metricsBtn.textContent = "メトリクスを更新";
  }
}

metricsBtn.addEventListener("click", updateMetrics);

// ===== 問い合わせ一覧 =====
const listBtn = document.getElementById("list-btn");
const searchBtn = document.getElementById("search-btn");
const resetBtn = document.getElementById("reset-btn");
const listResult = document.getElementById("list-result");
const listBody = document.getElementById("list-body");

// 検索・フィルター欄
const filterStatus = document.getElementById("filter-status");
const filterCategory = document.getElementById("filter-category");
const filterUrgency = document.getElementById("filter-urgency");
const filterKeyword = document.getElementById("filter-keyword");

// 現在適用中の絞り込み条件（空 = 全件）。
// updateList() はこの条件を使うので、検索後の自動更新でも条件が保たれる。
let currentFilters = {};

const STATUS_LABELS = {
  new: "未対応",
  in_progress: "対応中",
  closed: "完了",
};

// 入力欄から絞り込み条件を読み取る（空の項目は含めない）
function readFilters() {
  const filters = {};
  if (filterStatus.value) filters.status = filterStatus.value;
  if (filterCategory.value) filters.category = filterCategory.value;
  if (filterUrgency.value) filters.urgency = filterUrgency.value;
  const keyword = filterKeyword.value.trim();
  if (keyword) filters.keyword = keyword;
  return filters;
}

// 条件を GET /inquiries のURLに変換する（日本語キーワードも自動エンコード）
function buildInquiriesUrl(filters) {
  const params = new URLSearchParams(filters);
  const qs = params.toString();
  return qs ? `/inquiries?${qs}` : "/inquiries";
}

// 本文を短く表示する（長文で画面が崩れないように）
function truncate(text, max) {
  return text.length > max ? text.slice(0, max) + "…" : text;
}

// 作成日時を読みやすい日本語表記にする
function formatDateTime(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) {
    return escapeHtml(iso);
  }
  return d.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ステータス変更用の select を作る（現在の status を選択状態にする）
function statusSelectHtml(currentStatus) {
  const options = Object.keys(STATUS_LABELS)
    .map((value) => {
      const selected = value === currentStatus ? " selected" : "";
      return `<option value="${value}"${selected}>${STATUS_LABELS[value]}</option>`;
    })
    .join("");
  return `<select class="status-select">${options}</select>`;
}

function renderList(items) {
  if (items.length === 0) {
    // 絞り込み中なら「条件に一致なし」、無条件なら「まだ登録なし」を表示
    const isFiltering = Object.keys(currentFilters).length > 0;
    const message = isFiltering
      ? "条件に一致する問い合わせはありません。"
      : "まだ問い合わせがありません。";
    listBody.innerHTML = `<tr><td colspan="7" class="list-empty">${message}</td></tr>`;
    return;
  }

  listBody.innerHTML = items
    .map((item) => {
      const statusLabel = STATUS_LABELS[item.status] || item.status;
      const statusBadge =
        `<span class="badge badge-status-${escapeHtml(item.status)}">` +
        `${escapeHtml(statusLabel)}</span>`;

      // 最新カテゴリ（null は「未分類」）
      const categoryCell =
        item.latest_category === null
          ? '<span class="muted">未分類</span>'
          : `${escapeHtml(
              CATEGORY_LABELS[item.latest_category] || item.latest_category
            )}`;

      // 最新緊急度（null は「未分類」、値はバッジ表示）
      const urgencyCell =
        item.latest_urgency === null
          ? '<span class="muted">未分類</span>'
          : `<span class="badge badge-urgency-${escapeHtml(
              item.latest_urgency
            )}">${escapeHtml(
              URGENCY_LABELS[item.latest_urgency] || item.latest_urgency
            )}</span>`;

      const actionCell =
        `<div class="status-action">` +
        statusSelectHtml(item.status) +
        `<button class="btn btn-sm status-update-btn" type="button" ` +
        `data-id="${item.id}">更新</button>` +
        `</div>`;

      return (
        "<tr>" +
        `<td>${item.id}</td>` +
        `<td class="body-cell">${escapeHtml(truncate(item.body, 40))}</td>` +
        `<td>${statusBadge}</td>` +
        `<td>${categoryCell}</td>` +
        `<td>${urgencyCell}</td>` +
        `<td>${formatDateTime(item.created_at)}</td>` +
        `<td>${actionCell}</td>` +
        "</tr>"
      );
    })
    .join("");
}

// ステータス更新（行の「更新」ボタンから呼ばれる）
async function changeStatus(inquiryId, newStatus, button) {
  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = "更新中...";

  try {
    const res = await fetch(
      `/inquiries/${encodeURIComponent(inquiryId)}/status`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      }
    );

    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }

    if (!res.ok) {
      const detail = data && data.detail ? String(data.detail) : "";

      if (res.status === 404) {
        showResult(
          listResult,
          "error",
          "指定した問い合わせIDが見つかりません。" +
            (detail ? detailLine(detail) : "")
        );
        return;
      }

      // 不正な status（400）など
      showResult(
        listResult,
        "error",
        "ステータスの更新に失敗しました。" + (detail ? detailLine(detail) : "")
      );
      return;
    }

    const statusLabel = STATUS_LABELS[data.status] || data.status;
    showResult(
      listResult,
      "success",
      `ステータスを更新しました（ID: ${data.id} → ${escapeHtml(statusLabel)}）。`
    );

    // 更新後は一覧とメトリクスを最新化する
    await updateList();
    updateMetrics();
  } catch (err) {
    showResult(
      listResult,
      "error",
      "通信に失敗しました。サーバーが起動しているか確認してください。" +
        detailLine(String(err))
    );
  } finally {
    // updateList() で行が再生成される場合もあるが、
    // 失敗時に残った同じボタンのために元に戻しておく
    button.disabled = false;
    button.textContent = originalText;
  }
}

// 行が再生成されても効くよう、tbody にイベント委譲する
listBody.addEventListener("click", (event) => {
  const button = event.target.closest(".status-update-btn");
  if (!button) {
    return;
  }
  const row = button.closest("tr");
  const select = row.querySelector(".status-select");
  changeStatus(button.dataset.id, select.value, button);
});

// 一覧を取得する。成功したら true、失敗したら false を返す。
async function updateList() {
  listBtn.disabled = true;
  listBtn.textContent = "更新中...";

  try {
    // 現在の絞り込み条件を反映したURLで取得する
    const res = await fetch(buildInquiriesUrl(currentFilters));
    if (!res.ok) {
      showResult(
        listResult,
        "error",
        `一覧の取得に失敗しました（HTTP ${res.status}）。`
      );
      return false;
    }
    const data = await res.json();
    renderList(data);
    listResult.hidden = true;
    return true;
  } catch (err) {
    showResult(
      listResult,
      "error",
      "通信に失敗しました。サーバーが起動しているか確認してください。" +
        detailLine(String(err))
    );
    return false;
  } finally {
    listBtn.disabled = false;
    listBtn.textContent = "一覧を更新";
  }
}

// 「検索」ボタン: 入力欄の条件を確定して一覧を取得する
async function searchInquiries() {
  searchBtn.disabled = true;
  searchBtn.textContent = "検索中...";
  try {
    currentFilters = readFilters();
    await updateList();
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = "検索";
  }
}

// 「条件をリセット」ボタン: 入力欄と条件を空に戻して全件表示する
async function resetFilters() {
  resetBtn.disabled = true;
  resetBtn.textContent = "リセット中...";
  try {
    // 入力欄を初期状態（すべて / 空）に戻す
    filterStatus.value = "";
    filterCategory.value = "";
    filterUrgency.value = "";
    filterKeyword.value = "";

    // 絞り込み条件を空にして全件取得する
    currentFilters = {};
    const ok = await updateList();

    // 取得に成功したときだけ、リセット完了メッセージを表示する
    // （失敗時は updateList() のエラー表示を残す）
    if (ok) {
      showResult(listResult, "success", "検索条件をリセットしました。");
    }
  } finally {
    resetBtn.disabled = false;
    resetBtn.textContent = "条件をリセット";
  }
}

listBtn.addEventListener("click", updateList);
searchBtn.addEventListener("click", searchInquiries);
resetBtn.addEventListener("click", resetFilters);

// ページ読み込み時に一度だけ初期表示する
updateMetrics();
updateList();
