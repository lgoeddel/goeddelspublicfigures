import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import base64

# Set page configuration and theme
st.set_page_config(
    page_title="JHU Cardiac Surgery Risk Calculator",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom changes to enhance the appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #001F5B;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #001F5B;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .result-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
    }
    .risk-high {
        color: #d9534f;
        font-weight: bold;
        font-size: 2rem;
    }
    .risk-medium {
        color: #f0ad4e;
        font-weight: bold;
        font-size: 2rem;
    }
    .risk-low {
        color: #5cb85c;
        font-weight: bold;
        font-size: 2rem;
    }
    .info-box {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .slider-label {
        font-weight: 600;
    }
    .disclaimer {
        font-size: 0.8rem;
        color: #6c757d;
        text-align: center;
        margin-top: 2rem;
        font-style: italic;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #001F5B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Function to create a visual header with JHU
def create_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<div class="main-header">Johns Hopkins University<br>Post-Operative Cardiac Surgery Risk Calculator</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #6c757d;">Evidence-based mortality risk assessment for cardiac surgery patients</div>', unsafe_allow_html=True)

# Function to calculate adjusted age coefficient
def calculate_age_coefficient(age, base_coefficient):
    if age < 60:
        return base_coefficient
    else:
        years_over_59 = age - 59
        return (1 + years_over_59) * base_coefficient

# Logistic regression calculation based off prior data published coefficients
def calculate_predicted_mortality(inputs):
    beta_0 = -4.789594  # Intercept
    # Coefficients from the table (updated)
    coefficients = {
        "age": 0.0666354,
        "female": 0.3304052,
        "creatinine": 0.6521653,
        "arteriopathy": 0.6558917,
        "pulmonary_disease": 0.4931341,
        "neurological_dysfunction": 0.841626,
        "previous_cardiac_surgery": 1.002625,
        "recent_mi": 0.5460218,
        "lvef_30_50": 0.4191643,
        "lvef_less_30": 1.094443,
        "pulmonary_pressure": 0.7676924,
        "active_endocarditis": 1.101265,
        "unstable_angina": 0.5677075,
        "emergency_op": 0.7127953,
        "critical_preop_state": 0.9058132,
        "ventricular_septal_rupture": 1.462009,
        "non_isolated_coronary_surgery": 0.5420364,
        "thoracic_aortic_surgery": 1.159787,
    }

    # Sum up all contributions to the logit
    logit = beta_0
    contributions = {}
    for var, coeff in coefficients.items():
        if var == "age":
            age_coeff = calculate_age_coefficient(inputs["age"], coeff)
            logit += age_coeff
            contributions["Age"] = age_coeff
        elif var in inputs and inputs[var]:
            logit += coeff
            # Map variable names to more readable format for the chart
            readable_names = {
                "female": "Female Gender",
                "creatinine": "High Creatinine",
                "arteriopathy": "Extracardiac Arteriopathy",
                "pulmonary_disease": "Pulmonary Disease",
                "neurological_dysfunction": "Neurological Dysfunction",
                "previous_cardiac_surgery": "Previous Cardiac Surgery",
                "recent_mi": "Recent MI",
                "lvef_30_50": "LVEF 30-50%",
                "lvef_less_30": "LVEF <30%",
                "pulmonary_pressure": "High Pulmonary Pressure",
                "active_endocarditis": "Active Endocarditis",
                "unstable_angina": "Unstable Angina",
                "emergency_op": "Emergency Operation",
                "critical_preop_state": "Critical Preoperative State",
                "ventricular_septal_rupture": "Ventricular Septal Rupture",
                "non_isolated_coronary_surgery": "Non-isolated Coronary Surgery",
                "thoracic_aortic_surgery": "Thoracic Aortic Surgery",
            }
            contributions[readable_names[var]] = coeff

    # Logistic regression formula
    mortality_risk = np.exp(logit) / (1 + np.exp(logit))
    return mortality_risk, contributions

# Function to create risk visualization
def create_risk_visualization(risk, contributions):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [1, 2]})
    
    # Create a gauge chart for risk
    gauge_colors = ['#5cb85c', '#f0ad4e', '#d9534f']
    risk_percentage = risk * 100
    
    # Determine color based on risk level
    if risk_percentage < 5:
        color = gauge_colors[0]  # green
        risk_level = "Low"
    elif risk_percentage < 15:
        color = gauge_colors[1]  # yellow
        risk_level = "Medium"
    else:
        color = gauge_colors[2]  # red
        risk_level = "High"
    
    # Create gauge chart
    ax1.pie([risk_percentage, 100-risk_percentage], colors=[color, '#f8f9fa'], 
            startangle=90, counterclock=False,
            wedgeprops={'width': 0.3, 'edgecolor': 'w', 'linewidth': 2})
    ax1.add_artist(plt.Circle((0, 0), 0.3, fc='white'))
    ax1.text(0, 0, f"{risk_percentage:.2f}%", ha='center', va='center', fontsize=20, fontweight='bold')
    ax1.text(0, -0.2, f"{risk_level} Risk", ha='center', va='center', fontsize=14, color=color)
    ax1.set_title('Mortality Risk', fontsize=16, pad=20)
    
    # Create horizontal bar chart for risk factors
    if contributions:
        # Sort contributions by value
        sorted_contrib = {k: v for k, v in sorted(contributions.items(), key=lambda item: item[1], reverse=True)}
        names = list(sorted_contrib.keys())
        values = list(sorted_contrib.values())
        
        # Only show top 10 contributors
        if len(names) > 10:
            names = names[:10]
            values = values[:10]
        
        bars = ax2.barh(names, values, color='#001F5B', alpha=0.7)
        ax2.set_xlabel('Contribution to Risk Score')
        ax2.set_title('Top Risk Factors', fontsize=16, pad=20)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax2.text(width + 0.01, bar.get_y() + bar.get_height()/2, f"{width:.2f}", 
                     va='center', fontsize=10)
    
    plt.tight_layout()
    return fig

# Main application
def main():
    create_header()
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Risk Calculator", "About This Tool", "Glossary"])
    
    with tab1:
        # Create two columns
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown('<div class="sub-header">Patient Information</div>', unsafe_allow_html=True)
            
            # Demographic information
            age = st.slider("Age (years)", 18, 100, 60, help="Patient's age in years")
            gender = st.radio("Gender", ["Male", "Female"])
            inputs = {"age": age, "female": gender == "Female"}
            
            # Create expandable sections for different risk categories
            with st.expander("Renal Function", expanded=True):
                inputs["creatinine"] = st.checkbox("Serum creatinine >2.2 µg/dL", 
                                                 help="Moderately impaired renal function or patient on dialysis")
            
            with st.expander("Cardiovascular Conditions", expanded=True):
                inputs["arteriopathy"] = st.checkbox("Extracardiac arteriopathy", 
                                                    help="Claudication, carotid occlusion or stenosis, previous or planned vascular surgery")
                inputs["previous_cardiac_surgery"] = st.checkbox("Previous cardiac surgery", 
                                                              help="Previous surgery requiring opening of the pericardium")
                inputs["recent_mi"] = st.checkbox("Recent myocardial infarct", 
                                               help="Myocardial infarct within 90 days prior to surgery")
                inputs["unstable_angina"] = st.checkbox("Unstable angina", 
                                                     help="Rest angina requiring IV nitrates until arrival in operating room")
                
                # LVEF selection with more visual indicator
                st.markdown('<span class="slider-label">Left Ventricular Ejection Fraction (LVEF)</span>', unsafe_allow_html=True)
                lvef_cols = st.columns(3)
                with lvef_cols[0]:
                    lvef_normal = st.checkbox("Normal (>50%)")
                with lvef_cols[1]:
                    lvef_moderate = st.checkbox("Moderate (30-50%)")
                with lvef_cols[2]:
                    lvef_poor = st.checkbox("Poor (<30%)")
                
                # Make sure only one LVEF option is selected
                if sum([lvef_normal, lvef_moderate, lvef_poor]) > 1:
                    st.warning("Please select only one LVEF range")
                
                inputs["lvef_30_50"] = lvef_moderate
                inputs["lvef_less_30"] = lvef_poor
                
                inputs["pulmonary_pressure"] = st.checkbox("Systolic pulmonary pressure >60 mmHg")
                inputs["ventricular_septal_rupture"] = st.checkbox("Ventricular septal rupture")
            
            with st.expander("Pulmonary & Neurological Status", expanded=True):
                inputs["pulmonary_disease"] = st.checkbox("Pulmonary disease", 
                                                       help="Long-term use of bronchodilators or steroids for lung disease")
                inputs["neurological_dysfunction"] = st.checkbox("Neurological dysfunction", 
                                                             help="Severely affecting ambulation or day-to-day functioning")
            
            with st.expander("Infection & Critical Status", expanded=True):
                inputs["active_endocarditis"] = st.checkbox("Active endocarditis", 
                                                         help="Patient still under antibiotic treatment for endocarditis at time of surgery")
                inputs["critical_preop_state"] = st.checkbox("Critical preoperative state", 
                                                          help="Ventricular tachycardia, fibrillation, aborted sudden death, CPR, ventilation, inotropic support, IABP, acute renal failure")
            
            with st.expander("Procedure Information", expanded=True):
                inputs["emergency_op"] = st.checkbox("Emergency operation", 
                                                  help="Surgery required before the beginning of the next working day")
                inputs["non_isolated_coronary_surgery"] = st.checkbox("Other than isolated coronary surgery")
                inputs["thoracic_aortic_surgery"] = st.checkbox("Thoracic aortic surgery")
            
            # Button styling
            st.markdown("""
            <style>
                div.stButton > button {
                    background-color: #001F5B;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                    border: none;
                    width: 100%;
                    margin-top: 20px;
                }
                div.stButton > button:hover {
                    background-color: #003082;
                }
            </style>
            """, unsafe_allow_html=True)
            
            calculate_button = st.button("Calculate Risk")
        
        # Right column for results
        with col2:
            if calculate_button:
                risk, contributions = calculate_predicted_mortality(inputs)
                
                # Display risk with appropriate styling
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown('<div class="sub-header">Mortality Risk Assessment</div>', unsafe_allow_html=True)
                
                # Determine risk category for styling
                risk_class = "risk-low" if risk < 0.05 else "risk-medium" if risk < 0.15 else "risk-high"
                st.markdown(f'<div class="{risk_class}">{risk:.2%}</div>', unsafe_allow_html=True)
                
                # Risk interpretation
                if risk < 0.05:
                    st.markdown("**Low Risk**")
                    st.markdown("The predicted mortality risk is relatively low. However, all cardiac surgeries carry inherent risks.")
                elif risk < 0.15:
                    st.markdown("**Moderate Risk**")
                    st.markdown("The patient has an elevated risk of post-operative mortality. Consider additional preoperative optimization if possible.")
                else:
                    st.markdown("**High Risk**")
                    st.markdown("The patient has a significant risk of post-operative mortality. Consider additional preoperative optimization and/or alternative treatment approaches if appropriate.")
                
                # Visualization
                fig = create_risk_visualization(risk, contributions)
                st.pyplot(fig)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Additional information and considerations
                with st.expander("Interpretation Notes", expanded=True):
                    st.markdown("""
                    - This risk score represents an estimate of 30-day mortality risk following cardiac surgery
                    - The model is based on population data and individual results may vary
                    - Consider discussing specific risk factors with the patient
                    - This calculation should be used as one component of a comprehensive clinical assessment
                    """)
    
    # About tab content
    with tab2:
        st.markdown('<div class="sub-header">About the JHU Cardiac Surgery Risk Calculator</div>', unsafe_allow_html=True)
        st.markdown("""
        This tool provides an evidence-based estimation of post-operative mortality risk for patients undergoing 
        cardiac surgery. It is based on a modified version of the European System for Cardiac Operative Risk 
        Evaluation (EuroSCORE) methodology.
        
        ### Development and Validation
        
        The risk model was developed using data from a large cohort of cardiac surgery patients.
        
        ### Clinical Application
        
        This calculator is designed to:
        - Assist in preoperative risk assessment
        - Facilitate informed consent discussions with patients
        - Support clinical decision-making regarding surgical approach
        - Enable benchmarking and quality improvement initiatives
        
        ### Limitations
        
        While this tool provides valuable risk estimates, it has several limitations:
        - It does not capture all possible risk factors
        - It may not fully account for rare conditions or unique patient factors
        - The model is based on historical data and may not reflect the most recent advances in surgical technique
        - Risk calculations should always be interpreted in the context of clinical judgment
        """)
        
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **Note for Clinicians:**  
        This tool should be used as a supplement to, not a replacement for, comprehensive clinical evaluation. 
        Patient-specific factors not captured in this model may significantly impact surgical risk.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Glossary tab
    with tab3:
        st.markdown('<div class="sub-header">Glossary of Terms</div>', unsafe_allow_html=True)
        
        glossary = {
            "Extracardiac arteriopathy": "Disease affecting arteries outside the heart, including claudication, carotid occlusion or stenosis >50%, and previous or planned intervention on the abdominal aorta, limb arteries, or carotids.",
            "Critical preoperative state": "Any of the following: ventricular tachycardia or fibrillation or aborted sudden death, preoperative cardiac massage, preoperative ventilation before arrival in the anesthetic room, preoperative inotropic support, intraaortic balloon counterpulsation, or preoperative acute renal failure.",
            "Pulmonary hypertension": "Systolic pulmonary artery pressure >60 mmHg.",
            "Active endocarditis": "Patient still under antibiotic treatment for endocarditis at the time of surgery.",
            "Unstable angina": "Rest angina requiring intravenous nitrates until arrival in the operating room.",
            "LVEF": "Left Ventricular Ejection Fraction - the percentage of blood leaving the left ventricle when it contracts.",
            "Emergency operation": "Operation carried out before the beginning of the next working day after the decision to operate.",
            "Ventricular septal rupture": "A hole in the wall separating the ventricles that occurs after myocardial infarction."
        }
        
        # Display glossary terms in a more structured format
        for term, definition in glossary.items():
            st.markdown(f"**{term}**")
            st.markdown(f"{definition}")
            st.markdown("---")
    
    # Footer
    st.markdown('<div class="disclaimer">This calculator is provided for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()