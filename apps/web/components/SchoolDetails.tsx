/**
 * SchoolDetails Component
 *
 * Displays comprehensive information about a flight school,
 * including programs, pricing, and operational details.
 */

import { useState } from 'react';
import {
  GraduationCap,
  DollarSign,
  Clock,
  CheckCircle,
  X,
  ChevronDown,
  ChevronRight,
  Star,
  Award,
  Users,
  Plane,
  Calendar,
  MapPin,
  ExternalLink
} from 'lucide-react';

interface SchoolDetailsProps {
  school: any;
  programs?: any[];
  pricing?: any;
  metrics?: any;
  attributes?: any;
}

export default function SchoolDetails({
  school,
  programs,
  pricing,
  metrics,
  attributes
}: SchoolDetailsProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  return (
    <div className="space-y-6">
      {/* School Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{school.name}</h1>

              {/* Location and Rating */}
              <div className="flex items-center space-x-4 text-gray-600 mb-4">
                {school.location?.city && (
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-1" />
                    <span>{school.location.city}{school.location.state ? `, ${school.location.state}` : ''}</span>
                  </div>
                )}

                {school.googleRating && (
                  <div className="flex items-center">
                    <Star className="w-4 h-4 mr-1 text-yellow-500 fill-current" />
                    <span className="font-medium">{school.googleRating.toFixed(1)}</span>
                    {school.googleReviewCount && (
                      <span className="text-sm text-gray-500 ml-1">
                        ({school.googleReviewCount} reviews)
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Accreditation Badges */}
              <div className="flex items-center space-x-3 mb-4">
                {school.accreditation?.type && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    <Award className="w-4 h-4 mr-1" />
                    {school.accreditation.type}
                  </span>
                )}

                {school.accreditation?.vaApproved && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    VA Approved
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {school.description && (
            <div className="mb-6">
              <p className="text-gray-700 leading-relaxed">{school.description}</p>
            </div>
          )}

          {/* Specialties */}
          {school.specialties && school.specialties.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Specialties</h3>
              <div className="flex flex-wrap gap-2">
                {school.specialties.map((specialty: string, index: number) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700 border border-blue-200"
                  >
                    {specialty}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Programs Section */}
      {programs && programs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('programs')}
            className="w-full p-6 text-left border-b border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <GraduationCap className="w-5 h-5 mr-3 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900">Training Programs</h2>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                  {programs.length}
                </span>
              </div>
              {expandedSections.has('programs') ? (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-500" />
              )}
            </div>
          </button>

          {expandedSections.has('programs') && (
            <div className="p-6">
              <div className="grid gap-4 md:grid-cols-2">
                {programs.map((program: any) => (
                  <div key={program.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">{program.name}</h3>

                    {program.description && (
                      <p className="text-sm text-gray-600 mb-3">{program.description}</p>
                    )}

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center text-gray-600">
                        <Clock className="w-4 h-4 mr-2" />
                        <span>
                          {program.duration?.weeksTypical ? `${program.duration.weeksTypical} weeks` : 'Duration TBD'}
                        </span>
                      </div>

                      {program.aircraftTypes && program.aircraftTypes.length > 0 && (
                        <div className="flex items-center text-gray-600">
                          <Plane className="w-4 h-4 mr-2" />
                          <span>{program.aircraftTypes.join(', ')}</span>
                        </div>
                      )}

                      <div className="flex items-center space-x-2 mt-3">
                        {program.part61Available && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Part 61</span>
                        )}
                        {program.part141Available && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Part 141</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pricing Section */}
      {pricing && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('pricing')}
            className="w-full p-6 text-left border-b border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <DollarSign className="w-5 h-5 mr-3 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">Pricing Information</h2>
              </div>
              {expandedSections.has('pricing') ? (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-500" />
              )}
            </div>
          </button>

          {expandedSections.has('pricing') && (
            <div className="p-6">
              {/* Program Costs */}
              {pricing.programCosts && pricing.programCosts.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Program Costs</h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {pricing.programCosts.map((cost: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">{cost.programType}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            cost.costBand === 'budget' ? 'bg-green-100 text-green-800' :
                            cost.costBand === '$5k-$10k' ? 'bg-blue-100 text-blue-800' :
                            cost.costBand === '$10k-$15k' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {cost.costBand}
                          </span>
                        </div>
                        {cost.estimatedTotalTypical && (
                          <div className="text-sm text-gray-600">
                            Typical: ${cost.estimatedTotalTypical.toLocaleString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Hourly Rates */}
              {pricing.hourlyRates && pricing.hourlyRates.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Hourly Rates</h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {pricing.hourlyRates.map((rate: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="font-medium text-gray-900 mb-1">
                          {rate.aircraftCategory.replace('_', ' ').toUpperCase()}
                        </div>
                        <div className="text-lg font-semibold text-green-600">
                          ${rate.ratePerHour}/hr
                        </div>
                        {rate.includesInstructor && (
                          <div className="text-xs text-gray-600 mt-1">Includes instructor</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Package Pricing */}
              {pricing.packagePricing && pricing.packagePricing.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Package Deals</h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {pricing.packagePricing.map((pkg: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-2">{pkg.packageName}</h4>
                        <div className="text-lg font-semibold text-green-600 mb-1">
                          ${pkg.totalCost.toLocaleString()}
                        </div>
                        {pkg.flightHoursIncluded && (
                          <div className="text-sm text-gray-600">
                            Includes {pkg.flightHoursIncluded} flight hours
                          </div>
                        )}
                        {pkg.validForMonths && (
                          <div className="text-xs text-gray-500 mt-1">
                            Valid for {pkg.validForMonths} months
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Additional Fees */}
              {pricing.additionalFees && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Additional Fees</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {pricing.additionalFees.checkrideFee && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Checkride Fee</span>
                        <span className="font-medium">${pricing.additionalFees.checkrideFee}</span>
                      </div>
                    )}
                    {pricing.additionalFees.medicalExamFee && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Medical Exam</span>
                        <span className="font-medium">${pricing.additionalFees.medicalExamFee}</span>
                      </div>
                    )}
                    {pricing.additionalFees.knowledgeTestFee && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Knowledge Test</span>
                        <span className="font-medium">${pricing.additionalFees.knowledgeTestFee}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Operational Information */}
      {school.operations && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('operations')}
            className="w-full p-6 text-left border-b border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Users className="w-5 h-5 mr-3 text-purple-600" />
                <h2 className="text-xl font-semibold text-gray-900">Operations & Capacity</h2>
              </div>
              {expandedSections.has('operations') ? (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-500" />
              )}
            </div>
          </button>

          {expandedSections.has('operations') && (
            <div className="p-6">
              <div className="grid gap-6 md:grid-cols-2">
                {school.operations.foundedYear && (
                  <div className="flex items-center">
                    <Calendar className="w-5 h-5 mr-3 text-gray-400" />
                    <div>
                      <div className="font-medium text-gray-900">Founded</div>
                      <div className="text-sm text-gray-600">{school.operations.foundedYear}</div>
                    </div>
                  </div>
                )}

                {school.operations.fleetSize && (
                  <div className="flex items-center">
                    <Plane className="w-5 h-5 mr-3 text-gray-400" />
                    <div>
                      <div className="font-medium text-gray-900">Fleet Size</div>
                      <div className="text-sm text-gray-600">{school.operations.fleetSize} aircraft</div>
                    </div>
                  </div>
                )}

                {school.operations.employeeCount && (
                  <div className="flex items-center">
                    <Users className="w-5 h-5 mr-3 text-gray-400" />
                    <div>
                      <div className="font-medium text-gray-900">Staff</div>
                      <div className="text-sm text-gray-600">{school.operations.employeeCount} employees</div>
                    </div>
                  </div>
                )}

                {school.operations.studentCapacity && (
                  <div className="flex items-center">
                    <GraduationCap className="w-5 h-5 mr-3 text-gray-400" />
                    <div>
                      <div className="font-medium text-gray-900">Capacity</div>
                      <div className="text-sm text-gray-600">{school.operations.studentCapacity} students</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Location Details */}
      {school.location && (school.location.address || school.location.nearestAirportIcao) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('location')}
            className="w-full p-6 text-left border-b border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <MapPin className="w-5 h-5 mr-3 text-red-600" />
                <h2 className="text-xl font-semibold text-gray-900">Location Details</h2>
              </div>
              {expandedSections.has('location') ? (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-500" />
              )}
            </div>
          </button>

          {expandedSections.has('location') && (
            <div className="p-6">
              <div className="grid gap-4 md:grid-cols-2">
                {school.location.address && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Address</h3>
                    <p className="text-gray-600">{school.location.address}</p>
                    {school.location.city && school.location.state && (
                      <p className="text-gray-600">
                        {school.location.city}, {school.location.state} {school.location.zipCode}
                      </p>
                    )}
                  </div>
                )}

                {(school.location.nearestAirportIcao || school.location.nearestAirportName) && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Nearest Airport</h3>
                    {school.location.nearestAirportIcao && (
                      <p className="text-gray-600 font-mono">{school.location.nearestAirportIcao}</p>
                    )}
                    {school.location.nearestAirportName && (
                      <p className="text-gray-600">{school.location.nearestAirportName}</p>
                    )}
                    {school.location.airportDistanceMiles && (
                      <p className="text-sm text-gray-500">
                        {school.location.airportDistanceMiles} miles away
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
