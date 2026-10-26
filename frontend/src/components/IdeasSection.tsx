import React, { useState } from "react";
import { GroupedIdeas, IdeaItem } from "../repository/types";

interface IdeasSectionProps {
  ideas: GroupedIdeas;
}

export const IdeasSection: React.FC<IdeasSectionProps> = ({ ideas }) => {
  const [activeTab, setActiveTab] = useState<keyof GroupedIdeas>("food");

  const tabs: { key: keyof GroupedIdeas; label: string; icon: string }[] = [
    { key: "food", label: "Food & Catering", icon: "🍛" },
    { key: "decor", label: "Décor & Ambience", icon: "🌸" },
    { key: "activities", label: "Activities & Fun", icon: "🎶" },
    { key: "themes", label: "Theme & Palette", icon: "🎨" },
    { key: "logistics", label: "Logistics & Flow", icon: "📋" },
  ];

  const currentList: IdeaItem[] = ideas[activeTab] || [];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8 space-y-6">
      <div className="border-b border-stone-100 pb-4">
        <h2 className="text-xl font-bold text-stone-900">Personalized Ideas & Cultural Inspirations</h2>
        <p className="text-xs text-stone-500 mt-0.5">
          Curated suggestions crafted specifically around your selected city, theme, and dietary requirements.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-stone-200 pb-2">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          const count = (ideas[tab.key] || []).length;

          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? "bg-orange-600 text-white shadow-sm"
                  : "bg-stone-100 text-stone-600 hover:bg-stone-200/80"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              <span
                className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] ${
                  isActive ? "bg-orange-700 text-white" : "bg-stone-200 text-stone-700"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Idea Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {currentList.length === 0 ? (
          <p className="text-sm text-stone-400 italic col-span-2 py-4">No ideas recorded in this category.</p>
        ) : (
          currentList.map((idea, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl border border-stone-200 bg-stone-50/50 hover:bg-stone-50 transition-colors flex flex-col justify-between space-y-3"
            >
              <div>
                <h4 className="font-bold text-stone-900 text-sm mb-1.5">{idea.title}</h4>
                <p className="text-xs text-stone-600 leading-relaxed">{idea.description}</p>
              </div>

              {idea.practical_tip && (
                <div className="p-2.5 rounded-lg bg-orange-50/80 border border-orange-200/60 text-orange-950 text-xs">
                  <span className="font-bold text-orange-800">💡 Practical Tip: </span>
                  {idea.practical_tip}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
