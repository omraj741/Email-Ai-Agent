import { useState } from "react";

const N8N_WEBHOOK_URL =
  "https://omraj68.app.n8n.cloud/webhook-test/n8n";

function App() {
  // State keeps the input, conversation messages, and request status up to date.
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([
    { sender: "You", text: "Hello" },
    { sender: "Bot", text: "Hello! How can I help you?" },
    { sender: "You", text: "What is React?" },
    { sender: "Bot", text: "React is a JavaScript library..." },
  ]);
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    const userMessage = message.trim();

    // Do not send blank messages or start a second request while one is active.
    if (!userMessage || loading) {
      return;
    }

    setChat((currentChat) => [
      ...currentChat,
      { sender: "You", text: userMessage },
    ]);
    setMessage("");
    setLoading(true);

    try {
      // Send the user's message to the n8n Webhook and wait for its JSON reply.
      const response = await fetch(N8N_WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      setChat((currentChat) => [
        ...currentChat,
        { sender: "Bot", text: data.output },
      ]);
    } catch (error) {
      // Keep the technical error in DevTools while showing a friendly message.
      console.error("n8n request failed:", error);
      setChat((currentChat) => [
        ...currentChat,
        { sender: "Bot", text: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      sendMessage();
    }
  }

  return (
    <main>
      <h1>Simple Chat</h1>

      <section aria-label="Conversation">
        {chat.map((chatMessage, index) => (
          <p key={index}>
            <strong>{chatMessage.sender}:</strong> {chatMessage.text}
          </p>
        ))}
        {loading && <p>Bot is typing...</p>}
      </section>

      <input
        type="text"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        aria-label="Message"
        disabled={loading}
      />
      <button type="button" onClick={sendMessage} disabled={loading}>
        Send
      </button>
    </main>
  );
}

export default App;
