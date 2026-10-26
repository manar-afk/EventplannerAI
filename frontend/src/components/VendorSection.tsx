import React, { useState } from "react";
import { VendorItem, VendorStatus } from "../repository/types";
import { formatINR } from "../utils/currency";

interface VendorSectionProps {
  vendors: VendorItem[];
  onUpdateVendorStatus: (id: string, status: VendorStatus) => void;
  onAddVendor: (vendor: Omit<VendorItem, "id">) => void;
}

export const VendorSection: React.FC<VendorSectionProps> = ({
  vendors,
  onUpdateVendorStatus,
  onAddVendor,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [category, setCategory] = useState("Catering");
  const [serviceName, setServiceName] = useState("");
  const [estimatedCost, setEstimatedCost] = useState<number>(25000);
  const [contactNotes, setContactNotes] = useState("");

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!serviceName.trim()) return;

    onAddVendor({
      category: category.trim(),
      service_name: serviceName.trim(),
      estimated_cost: Math.max(0, Math.round(estimatedCost)),
      status: "not_contacted",
      contact_notes: contactNotes.trim(),
    });

    setIsAdding(false);
    setServiceName("");
    setContactNotes("");
    setEstimatedCost(25000);
  };

  const getStatusBadge = (status: VendorStatus) => {
    switch (status) {
      case "booked":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "quoted":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "contacted":
        return "bg-purple-100 text-purple-800 border-purple-300";
      default:
        return "bg-stone-100 text-stone-700 border-stone-300";
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-100 pb-4">
        <div>
          <h2 className="text-xl font-bold text-stone-900">Vendor Checklist & Booking</h2>
          <p className="text-xs text-stone-500 mt-0.5">
            Track inquiries, quotes, and confirmed bookings across all event services.
          </p>
        </div>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="px-4 py-2 text-sm font-semibold text-orange-700 bg-orange-50 hover:bg-orange-100 rounded-xl border border-orange-200 transition-colors self-start md:self-auto"
        >
          {isAdding ? "Cancel" : "+ Add Vendor"}
        </button>
      </div>

      {/* Add Vendor Form */}
      {isAdding && (
        <form onSubmit={handleAddSubmit} className="p-4 bg-orange-50/40 border border-orange-200 rounded-xl space-y-3">
          <h4 className="text-sm font-bold text-orange-900">Add New Vendor to Checklist</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Service / Vendor Name</label>
              <input
                type="text"
                required
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. Royal Shehnai & Dhol"
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Category</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Catering, Photography..."
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Estimated Budget (INR)</label>
              <input
                type="number"
                min={0}
                step={1000}
                value={estimatedCost}
                onChange={(e) => setEstimatedCost(Number(e.target.value))}
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div className="sm:col-span-3">
              <label className="block text-xs font-semibold text-stone-600 mb-1">Contact Notes / References</label>
              <input
                type="text"
                value={contactNotes}
                onChange={(e) => setContactNotes(e.target.value)}
                placeholder="Phone number, portfolio link, or recommendations"
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-3 py-1 text-xs text-stone-600 hover:text-stone-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-semibold"
            >
              Add Vendor
            </button>
          </div>
        </form>
      )}

      {/* Vendor List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {vendors.map((vendor) => (
          <div
            key={vendor.id}
            className="p-4 rounded-xl border border-stone-200 hover:border-stone-300 transition-colors bg-white flex flex-col justify-between space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-xs font-medium text-stone-500 uppercase tracking-wider">
                  {vendor.category}
                </span>
                <h4 className="font-bold text-stone-900 text-sm">{vendor.service_name}</h4>
              </div>
              <span className="font-mono text-sm font-bold text-stone-800">
                {formatINR(vendor.estimated_cost)}
              </span>
            </div>

            {vendor.contact_notes && (
              <p className="text-xs text-stone-600 bg-stone-50 p-2 rounded-lg border border-stone-100">
                {vendor.contact_notes}
              </p>
            )}

            <div className="flex items-center justify-between pt-1 border-t border-stone-100">
              <span className="text-xs text-stone-500">Status:</span>
              <select
                value={vendor.status}
                onChange={(e) => onUpdateVendorStatus(vendor.id, e.target.value as VendorStatus)}
                className={`text-xs font-semibold px-2.5 py-1 rounded-lg border focus:outline-none focus:ring-2 focus:ring-orange-500 ${getStatusBadge(
                  vendor.status
                )}`}
              >
                <option value="not_contacted">Not Contacted</option>
                <option value="contacted">Contacted</option>
                <option value="quoted">Quoted</option>
                <option value="booked">Booked & Confirmed</option>
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
