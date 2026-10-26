import React, { useState } from "react";
import { EventCreateInput, EventType } from "../repository/types";
import { formatINR, formatCompactINR } from "../utils/currency";
import { getTodayIsoDate } from "../utils/dates";

interface EventFormProps {
  onSubmit: (data: EventCreateInput) => Promise<void>;
  isLoading: boolean;
  initialValues?: Partial<EventCreateInput>;
}

export const EventForm: React.FC<EventFormProps> = ({
  onSubmit,
  isLoading,
  initialValues
}) => {
  const todayStr = getTodayIsoDate();

  const [name, setName] = useState(initialValues?.name || "");
  const [eventType, setEventType] = useState<EventType>(initialValues?.event_type || "wedding");
  const [eventDate, setEventDate] = useState(initialValues?.event_date || "");
  const [location, setLocation] = useState(initialValues?.location || "");
  const [guestCount, setGuestCount] = useState<number>(initialValues?.guest_count || 150);
  const [totalBudget, setTotalBudget] = useState<number>(initialValues?.total_budget || 1000000);
  const [style, setStyle] = useState(initialValues?.style || "Traditional Elegance");
  const [theme, setTheme] = useState(initialValues?.theme || "Marigold & Royal Gold");
  const [specialRequirements, setSpecialRequirements] = useState(initialValues?.special_requirements || "");

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const errs: Record<string, string> = {};

    if (!name.trim()) {
      errs.name = "Event name is required.";
    } else if (name.length > 100) {
      errs.name = "Event name cannot exceed 100 characters.";
    }

    if (!eventDate) {
      errs.eventDate = "Event date is required.";
    } else if (eventDate < todayStr) {
      errs.eventDate = "Event date cannot be in the past. Please select today or a future date.";
    }

    if (!location.trim()) {
      errs.location = "City / Venue location is required.";
    } else if (location.length > 120) {
      errs.location = "Location cannot exceed 120 characters.";
    }

    if (!guestCount || guestCount < 1 || guestCount > 10000) {
      errs.guestCount = "Guest count must be between 1 and 10,000.";
    }

    if (!totalBudget || totalBudget < 1000 || totalBudget > 100000000) {
      errs.totalBudget = "Budget must be between ₹1,000 and ₹10,00,00,000 (10 Cr).";
    }

    if (specialRequirements.length > 500) {
      errs.specialRequirements = "Special requirements cannot exceed 500 characters.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    await onSubmit({
      name: name.trim(),
      event_type: eventType,
      event_date: eventDate,
      location: location.trim(),
      guest_count: Number(guestCount),
      total_budget: Number(totalBudget),
      style: style.trim(),
      theme: theme.trim(),
      special_requirements: specialRequirements.trim()
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8 space-y-6">
      <div className="border-b border-stone-100 pb-4">
        <h2 className="text-xl font-bold text-stone-900 tracking-tight">Create Your Event Plan</h2>
        <p className="text-sm text-stone-500 mt-1">
          Provide your event parameters in Indian Rupees (INR). Gemini AI will generate tailored budget allocations, vendors, and milestone schedules.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Event Name */}
        <div className="col-span-1 md:col-span-2">
          <label htmlFor="name" className="block text-sm font-semibold text-stone-700 mb-1">
            Event Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Priya & Arjun's Sangeet & Wedding"
            maxLength={100}
            className={`w-full px-4 py-2.5 rounded-xl border text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-orange-500 ${
              errors.name ? "border-red-400 bg-red-50/30" : "border-stone-300"
            }`}
          />
          {errors.name && <p className="text-red-600 text-xs mt-1">{errors.name}</p>}
        </div>

        {/* Event Type */}
        <div>
          <label htmlFor="eventType" className="block text-sm font-semibold text-stone-700 mb-1">
            Event Type <span className="text-red-500">*</span>
          </label>
          <select
            id="eventType"
            value={eventType}
            onChange={(e) => setEventType(e.target.value as EventType)}
            className="w-full px-4 py-2.5 rounded-xl border border-stone-300 bg-white text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="wedding">Wedding & Sangeet</option>
            <option value="birthday">Birthday & Milestone Party</option>
            <option value="community">Community / Cultural Festival</option>
          </select>
        </div>

        {/* Event Date (IST) */}
        <div>
          <label htmlFor="eventDate" className="block text-sm font-semibold text-stone-700 mb-1">
            Event Date (IST) <span className="text-red-500">*</span>
          </label>
          <input
            id="eventDate"
            type="date"
            min={todayStr}
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
            className={`w-full px-4 py-2.5 rounded-xl border text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500 ${
              errors.eventDate ? "border-red-400 bg-red-50/30" : "border-stone-300"
            }`}
          />
          {errors.eventDate && <p className="text-red-600 text-xs mt-1">{errors.eventDate}</p>}
        </div>

        {/* Location */}
        <div>
          <label htmlFor="location" className="block text-sm font-semibold text-stone-700 mb-1">
            City / Venue (India) <span className="text-red-500">*</span>
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Udaipur, Rajasthan or Bengaluru"
            maxLength={120}
            className={`w-full px-4 py-2.5 rounded-xl border text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-orange-500 ${
              errors.location ? "border-red-400 bg-red-50/30" : "border-stone-300"
            }`}
          />
          {errors.location && <p className="text-red-600 text-xs mt-1">{errors.location}</p>}
        </div>

        {/* Guest Count */}
        <div>
          <label htmlFor="guestCount" className="block text-sm font-semibold text-stone-700 mb-1">
            Guest Count (1 – 10,000) <span className="text-red-500">*</span>
          </label>
          <input
            id="guestCount"
            type="number"
            min={1}
            max={10000}
            value={guestCount || ""}
            onChange={(e) => setGuestCount(Number(e.target.value))}
            className={`w-full px-4 py-2.5 rounded-xl border text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500 ${
              errors.guestCount ? "border-red-400 bg-red-50/30" : "border-stone-300"
            }`}
          />
          {errors.guestCount && <p className="text-red-600 text-xs mt-1">{errors.guestCount}</p>}
        </div>

        {/* Total Budget INR */}
        <div className="col-span-1 md:col-span-2">
          <div className="flex justify-between items-center mb-1">
            <label htmlFor="totalBudget" className="block text-sm font-semibold text-stone-700">
              Total Budget in INR (₹) <span className="text-red-500">*</span>
            </label>
            <span className="text-xs font-bold text-orange-700 bg-orange-100 px-2.5 py-0.5 rounded-full">
              Preview: {formatINR(totalBudget || 0)} ({formatCompactINR(totalBudget || 0)})
            </span>
          </div>
          <input
            id="totalBudget"
            type="number"
            min={1000}
            max={100000000}
            step={1000}
            value={totalBudget || ""}
            onChange={(e) => setTotalBudget(Number(e.target.value))}
            className={`w-full px-4 py-2.5 rounded-xl border text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500 font-mono ${
              errors.totalBudget ? "border-red-400 bg-red-50/30" : "border-stone-300"
            }`}
          />
          <p className="text-xs text-stone-400 mt-1">
            Enter integer rupees. The budget engine calculates allocations, remaining balance, and over-budget checks deterministically.
          </p>
          {errors.totalBudget && <p className="text-red-600 text-xs mt-1">{errors.totalBudget}</p>}
        </div>

        {/* Style */}
        <div>
          <label htmlFor="style" className="block text-sm font-semibold text-stone-700 mb-1">
            Style Preference
          </label>
          <input
            id="style"
            type="text"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            placeholder="e.g. Royal Rajasthani or Modern Minimalist"
            maxLength={100}
            className="w-full px-4 py-2.5 rounded-xl border border-stone-300 text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>

        {/* Theme */}
        <div>
          <label htmlFor="theme" className="block text-sm font-semibold text-stone-700 mb-1">
            Theme / Palette
          </label>
          <input
            id="theme"
            type="text"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            placeholder="e.g. Marigold & Amber, Pastel Peach"
            maxLength={100}
            className="w-full px-4 py-2.5 rounded-xl border border-stone-300 text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>

        {/* Special Requirements */}
        <div className="col-span-1 md:col-span-2">
          <label htmlFor="specialRequirements" className="block text-sm font-semibold text-stone-700 mb-1">
            Special Requirements & Dietary Notes
          </label>
          <textarea
            id="specialRequirements"
            rows={2}
            value={specialRequirements}
            onChange={(e) => setSpecialRequirements(e.target.value)}
            placeholder="e.g. Strictly pure vegetarian Jain catering, wheelchair ramp required at mandap, pet-friendly lawn."
            maxLength={500}
            className="w-full px-4 py-2.5 rounded-xl border border-stone-300 text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
          />
          <p className="text-xs text-stone-400 mt-0.5 text-right">{specialRequirements.length} / 500 characters</p>
        </div>
      </div>

      <div className="pt-2 flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full md:w-auto px-8 py-3 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-semibold shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Generating Plan with Gemini...</span>
            </>
          ) : (
            <span>Generate Event Plan →</span>
          )}
        </button>
      </div>
    </form>
  );
};
