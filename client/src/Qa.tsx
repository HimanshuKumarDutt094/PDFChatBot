/// <reference types="vite-plugin-svgr/client" />

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "./components/ui/avatar";
import Send from "./assets/send.svg?react";
import CompanyLogo from "./assets/AILogo.svg?react";
type ChatEntry = {
  user: string;
  bot: string;
};

export default function Component() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append("files", selectedFiles[i]);
    }

    try {
      await axios.post(
        "https://pdfchatbot-production.up.railway.app/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      alert("Files uploaded successfully");
    } catch (error) {
      console.error("Error uploading files", error);
      alert("Failed to upload files");
    }
  };

  const handleAsk = async () => {
    try {
      const response = await axios.post(
        "https://pdfchatbot-production.up.railway.app/ask",
        { question },
        { headers: { "Content-Type": "application/json" } }
      );
      setChatHistory((prevHistory) => [
        ...prevHistory,
        { user: question, bot: response.data.answer },
      ]);
      setQuestion(""); // Clear the input field
    } catch (error) {
      console.error("Error asking question", error);
    }
  };

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory]);

  return (
    <div className="flex flex-col h-screen w-screen">
      <header className="flex items-center justify-between p-4 bg-white shadow">
        <div className="flex items-center space-x-2">
          {/* <img
            alt="Logo"
            className="h-8 w-8"
            height="30"
            src="."
            style={{ aspectRatio: "30/30", objectFit: "cover" }}
            width="30"
          /> */}
          <CompanyLogo />
          {/* <span className="text-lg font-semibold">planet</span>
          <span className="text-sm text-gray-500">formerly DPhi</span> */}
        </div>

        <div className="flex">
          <Input
            className="w-[5em]"
            type="file"
            multiple
            onChange={handleFileChange}
          />
          <Button variant="outline" onClick={handleUpload}>
            Upload
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col space-y-4">
          {chatHistory.map((entry, index) => (
            <span key={index}>
              <div className="flex items-start space-x-4 justify-end">
                <div className="bg-blue-500 text-white p-4 rounded-lg max-w-[70%]">
                  <p className="text-sm">{entry.user}</p>
                </div>
                <Avatar className="h-10 w-10">
                  <AvatarImage alt="User Avatar" src="/placeholder-user.jpg" />
                  <AvatarFallback>U</AvatarFallback>
                </Avatar>
              </div>
              <div className="flex items-start mt-2 space-x-4">
                <Avatar className="h-10 w-10">
                  <AvatarImage alt="Bot Avatar" src="src\assets\BotLogo.png" />
                  <AvatarFallback>B</AvatarFallback>
                </Avatar>
                <div className="bg-gray-100 p-4 rounded-lg max-w-[70%]">
                  <p className="text-sm">{entry.bot}</p>
                </div>
              </div>
            </span>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="flex items-center p-4 bg-white shadow">
        <Input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1"
          placeholder="Send a message..."
        />
        <Button className="ml-2" variant="outline" onClick={handleAsk}>
          <Send className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}
