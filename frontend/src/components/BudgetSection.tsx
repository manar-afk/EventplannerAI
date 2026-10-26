import React, { useState } from "react";
import { BudgetItem, BudgetCalculationResult, CostBasis } from "../repository/types";
import { formatINR, formatCompactINR } from "../utils/currency";

interface BudgetSectionProps {
  budget: BudgetCalculationResult;
  isRecalculating: boolean;
  onUpdateItems: (newItems: BudgetItem[]) => Promise<void>;
}

export const BudgetSection: React.FC<BudgetSectionProps> = ({
  budget,
  isRecalculating,
  onUpdateItems,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editCostBasis, setEditCostBasis] = useState<CostBasis>("fixed");
  const [editEstimate, setEditEstimate] = useState<number>(0);
  const [editActual, setEditActual] = useState<string>("");

  // Adding new item state
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("Catering");
  const [newCostBasis, setNewCostBasis] = useState<CostBasis>("fixed");
  const [newEstimate, setNewEstimate] = useState<number>(10000);

  const startEditing = (item: BudgetItem) => {
    setEditingId(item.id);
    setEditName(item.name);
    setEditCategory(item.category);
    setEditCostBasis(item.cost_basis);
    setEditEstimate(item.estimated_amount);
    setEditActual(item.actual_amount !== null ? String(item.actual_amount) : "");
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;

    const parsedActual = editActual.trim() === "" ? null : Math.max(0, parseInt(editActual, 10));

    const updated = budget.items.map((item) => {
      if (item.id === editingId) {
        return {
          ...item,
          name: editName.trim() || item.name,
          category: editCategory.trim() || item.category,
          cost_basis: editCostBasis,
          estimated_amount: Math.max(0, Math.round(editEstimate)),
          actual_amount: parsedActual !== null && !isNaN(parsedActual) ? parsedActual : null,
        };
      }
      return item;
    });

    setEditingId(null);
    await onUpdateItems(updated);
  };

  const handleRemoveItem = async (id: string) => {
    const updated = budget.items.filter((item) => item.id !== id);
    await onUpdateItems(updated);
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    const newItem: BudgetItem = {
      id: `bi-usr-${Date.now()}`,
      name: newName.trim(),
      category: newCategory.trim() || "General",
      cost_basis: newCostBasis,
      estimated_amount: Math.max(0, Math.round(newEstimate)),
      actual_amount: null,
      notes: "Custom user item",
    };

    setIsAdding(false);
    setNewName("");
    setNewEstimate(10000);
    await onUpdateItems([...budget.items, newItem]);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8 space-y-6">
      {/* Header and Recalculating Indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-100 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-stone-900">Budget Breakdown</h2>
            {isRecalculating && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 animate-pulse">
                <svg className="animate-spin h-3.5 w-3.5 text-orange-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                Recalculating via Python Engine...
              </span>
            )}
          </div>
          <p className="text-xs text-stone-500 mt-0.5">
            Values are verified in pure integer rupees. Estimates and actuals remain strictly separate.
          </p>
        </div>

        <button
          onClick={() => setIsAdding(!isAdding)}
          className="px-4 py-2 text-sm font-semibold text-orange-700 bg-orange-50 hover:bg-orange-100 rounded-xl border border-orange-200 transition-colors self-start md:self-auto"
        >
          {isAdding ? "Cancel" : "+ Add Budget Item"}
        </button>
      </div>

      {/* Over-budget Alert Banner */}
      {budget.is_over_budget && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-900 flex items-start gap-3 shadow-sm" role="alert">
          <span className="text-xl">⚠️</span>
          <div>
            <h4 className="font-bold text-sm">Budget Exceeded by {formatINR(budget.over_budget_amount)} ({formatCompactINR(budget.over_budget_amount)})</h4>
            <p className="text-xs text-red-700 mt-0.5">
              Current total planned or actual spend exceeds your target budget of {formatINR(budget.total_budget)}. Adjust item estimates or mark actual costs below.
            </p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Target */}
        <div className="p-4 bg-stone-50 border border-stone-200 rounded-xl">
          <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Total Target</p>
          <p className="text-lg md:text-xl font-bold text-stone-900 mt-1">{formatINR(budget.total_budget)}</p>
          <p className="text-xs text-stone-500 mt-0.5">{formatCompactINR(budget.total_budget)}</p>
        </div>

        {/* Total Planned */}
        <div className="p-4 bg-blue-50/60 border border-blue-200 rounded-xl">
          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Total Planned (Est.)</p>
          <p className="text-lg md:text-xl font-bold text-blue-900 mt-1">{formatINR(budget.total_planned)}</p>
          <p className="text-xs text-blue-600 mt-0.5">{formatCompactINR(budget.total_planned)}</p>
        </div>

        {/* Total Actual */}
        <div className="p-4 bg-purple-50/60 border border-purple-200 rounded-xl">
          <p className="text-xs font-semibold text-purple-700 uppercase tracking-wider">Actual Spent</p>
          <p className="text-lg md:text-xl font-bold text-purple-900 mt-1">{formatINR(budget.total_actual)}</p>
          <p className="text-xs text-purple-600 mt-0.5">{formatCompactINR(budget.total_actual)}</p>
        </div>

        {/* Remaining */}
        <div className={`p-4 border rounded-xl ${
          budget.remaining_budget < 0
            ? "bg-red-50/80 border-red-300 text-red-900"
            : "bg-emerald-50/80 border-emerald-300 text-emerald-900"
        }`}>
          <p className="text-xs font-semibold uppercase tracking-wider opacity-80">Remaining</p>
          <p className="text-lg md:text-xl font-bold mt-1">{formatINR(budget.remaining_budget)}</p>
          <p className="text-xs opacity-80 mt-0.5">{formatCompactINR(budget.remaining_budget)}</p>
        </div>
      </div>

      {/* Category Progress Bars */}
      <div className="space-y-3 pt-2">
        <h3 className="text-sm font-bold text-stone-800">Category Share</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {budget.categories.map((cat) => {
            const percentage = budget.total_budget > 0
              ? Math.min(100, Math.round((cat.planned_amount / budget.total_budget) * 100))
              : 0;

            return (
              <div key={cat.category} className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 text-xs">
                <div className="flex justify-between font-semibold text-stone-700 mb-1">
                  <span>{cat.category}</span>
                  <span>{formatINR(cat.planned_amount)} ({percentage}%)</span>
                </div>
                <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Item Modal / Inline Box */}
      {isAdding && (
        <form onSubmit={handleAddItem} className="p-4 bg-orange-50/40 border border-orange-200 rounded-xl space-y-3">
          <h4 className="text-sm font-bold text-orange-900">Add New Budget Item</h4>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-stone-600 mb-1">Item Name</label>
              <input
                type="text"
                required
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Traditional Dhol Troupe"
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Category</label>
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="Catering, Décor..."
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Cost Basis</label>
              <select
                value={newCostBasis}
                onChange={(e) => setNewCostBasis(e.target.value as CostBasis)}
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="fixed">Fixed</option>
                <option value="per_guest">Per Guest</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-600 mb-1">Estimated INR (₹)</label>
              <input
                type="number"
                min={0}
                step={500}
                value={newEstimate}
                onChange={(e) => setNewEstimate(Number(e.target.value))}
                className="w-full px-3 py-1.5 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange-500"
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
              disabled={isRecalculating}
              className="px-4 py-1.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-semibold"
            >
              Add Item
            </button>
          </div>
        </form>
      )}

      {/* Budget Items Table */}
      <div className="overflow-x-auto rounded-xl border border-stone-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-stone-100 text-stone-700 text-xs font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Item & Category</th>
              <th className="py-3 px-4">Cost Basis</th>
              <th className="py-3 px-4 text-right">Estimate (INR)</th>
              <th className="py-3 px-4 text-right">Actual (INR)</th>
              <th className="py-3 px-4 text-right">Effective</th>
              <th className="py-3 px-4 text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200 bg-white">
            {budget.items.map((item) => {
              const isEditingThis = editingId === item.id;
              const effectiveAmount = item.actual_amount !== null ? item.actual_amount : item.estimated_amount;

              if (isEditingThis) {
                return (
                  <tr key={item.id} className="bg-orange-50/50">
                    <td className="py-3 px-4">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full px-2 py-1 text-xs border rounded mb-1"
                        placeholder="Item name"
                      />
                      <input
                        type="text"
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="w-full px-2 py-1 text-xs border rounded text-stone-500"
                        placeholder="Category"
                      />
                    </td>
                    <td className="py-3 px-4">
                      <select
                        value={editCostBasis}
                        onChange={(e) => setEditCostBasis(e.target.value as CostBasis)}
                        className="px-2 py-1 text-xs border rounded bg-white"
                      >
                        <option value="fixed">Fixed</option>
                        <option value="per_guest">Per Guest</option>
                      </select>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <input
                        type="number"
                        min={0}
                        step={500}
                        value={editEstimate}
                        onChange={(e) => setEditEstimate(Number(e.target.value))}
                        className="w-28 px-2 py-1 text-xs border rounded text-right font-mono"
                      />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <input
                        type="number"
                        min={0}
                        step={500}
                        value={editActual}
                        onChange={(e) => setEditActual(e.target.value)}
                        placeholder="Enter actual"
                        className="w-28 px-2 py-1 text-xs border rounded text-right font-mono"
                      />
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-xs">
                      {formatINR(editActual ? Number(editActual) : editEstimate)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={handleSaveEdit}
                          disabled={isRecalculating}
                          className="px-2.5 py-1 text-xs bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="px-2 py-1 text-xs text-stone-600 hover:text-stone-900"
                        >
                          Cancel
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              }

              return (
                <tr key={item.id} className="hover:bg-stone-50/80 transition-colors">
                  <td className="py-3 px-4">
                    <p className="font-semibold text-stone-900">{item.name}</p>
                    <p className="text-xs text-stone-500">{item.category}</p>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                      item.cost_basis === "per_guest"
                        ? "bg-purple-100 text-purple-800"
                        : "bg-stone-100 text-stone-700"
                    }`}>
                      {item.cost_basis === "per_guest" ? "Per Guest" : "Fixed"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-stone-800">
                    {formatINR(item.estimated_amount)}
                  </td>
                  <td className="py-3 px-4 text-right font-mono">
                    {item.actual_amount !== null ? (
                      <span className="text-purple-700 font-semibold">{formatINR(item.actual_amount)}</span>
                    ) : (
                      <span className="text-stone-400 italic text-xs">Not recorded</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-stone-900">
                    {formatINR(effectiveAmount)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-3">
                      <button
                        onClick={() => startEditing(item)}
                        disabled={isRecalculating}
                        className="text-xs font-semibold text-orange-600 hover:text-orange-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        disabled={isRecalculating}
                        className="text-xs text-red-500 hover:text-red-700"
                        title="Remove item"
                      >
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
